from datetime import datetime
from lxml import etree
from lxml.builder import E
import urllib, urllib2, re
import xml2json
from urlparse import urlparse

def validXmlCharOrdinal(c):
	codepoint = ord(c)
	#Esto es para que a la hora de crear el xml, no tenga problemas con caracteres invalidos (Suponemos siguientes versiones de lxml sulucionara el problema)
	return (
		0x20 <= codepoint <= 0xD7FF or
		codepoint in (0x9, 0xA, 0xD) or
		0xE000 <= codepoint <= 0xFFFD or
		0x10000 <= codepoint <= 0x10FFFF
		)
	
def cleanStringToLXML(inputString):
		return ''.join(c for c in inputString if validXmlCharOrdinal(c))

class question():
	def __init__(self, qid, proxy = None):
		self.qid = qid
		self.url = "https://answers.yahoo.com/question/index?qid={}".format(qid)
		self.proxy = proxy
		if(not self.checkQID(qid)):
			#Existen QID mas antiguas que no siguen el formato (muy pocas)
			#para este caso se asume el costo de traer la primera pagina
			#y checar si existe el elemento tipo <meta property="og:question:published_time" content="2006-02-01T01:20:12Z">
			data = self.getSourceCode(self.url)
			xml = etree.HTML(data)
			fecha = xml.xpath("//meta[@property='og:question:published_time']")
			if(len(fecha) == 1):
				self.date = datetime.strptime(fecha[0].get("content"),"%Y-%m-%dT%H:%M:%SZ")
			else:
				self.__del__()

	def checkQID(self,qid):
		pattern = re.compile("^\d{14}\w{7}$")
		if(pattern.match(qid)):
			try:
				self.date = datetime.strptime(qid[:14],"%Y%m%d%H%M%S")
			except:
				return False
			return True
		else:
			return False
			
	def getSourceCode(self, url, timeOut = 3):
		#si proxy es distinto de None, tiene la forma
		#{"protocolo":"<protocolo>", "urlProxy":"<direccion del proxy: user:pass@url>", "puerto":"<puerto del proxy>"}
		#Ejemplo {"protocolo":"https", "urlProxy":"52.53.254.181", "puerto":"8083"}
		if(self.proxy is None):
			opener = urllib2.urlopen(url, timeout = timeOut)
			data = opener.read()
		else:
			proxy = urllib2.ProxyHandler({self.proxy["protocolo"]: "{}:{}".format(self.proxy["urlProxy"], self.proxy["puerto"])})
			opener = urllib2.build_opener(proxy)
			urllib2.install_opener(opener)
			data = urllib2.urlopen(url, timeout = timeOut).read()
		return data
	
	def getXML(self, _url = None, filtered = False):
		try:
			if(_url is None):
				datos = self.getSourceCode(self.url)
			else:
				datos = self.getSourceCode(_url)
		except Exception as E:
			datos = "<div></div>"
		if not hasattr(self, 'xml'):
			self.xml = []
		self.crawledDate = datetime.now()
		if(filtered):
			self.xml.append(etree.HTML(cleanStringToLXML(datos)))
		else:
			self.xml.append(etree.HTML(datos))
			
	def parseAtribs(self, atributos):
		salida = {}
		for elemento in atributos.split(";"):
			salida[elemento.split(":")[0]] = elemento.split(":")[1]
		return salida
			
	def getCategory(self):
		if hasattr(self, 'xml'):
			categorias = []
			categoria = self.xml[0].xpath("//div[@id='brdCrb']")
			if(len(categoria)!=1):
				return None
			else:
				categoria = categoria[0].findall("a")
				for elemento in categoria:
					categorias.append((self.parseAtribs(elemento.attrib['data-ylk'])["catId"],elemento.text))
				self.categories = categorias
				return True
		else:
			self.getXML()
			self.getCategory()

	def getFollowers(self):
		if hasattr(self, 'xml'):
			buff = self.xml[0].xpath("//span[@class='follow-text']")
			if(len(buff) == 1):
				self.followers = int(buff[0].get("data-ya-fc"))
			else:
				self.followers = None
		else:
			self.getXML()
			self.getCategory()

#Canonical se refiere al idioma de la pregunta y en que lenguaje de yahoo se encuentra
	def getCanonical(self):
		if hasattr(self, 'xml'):
			canonical = self.xml[0].xpath("//link[@rel='canonical']")
			if(len(canonical) != 1):
				return None
			canonical = canonical[0]
			self.urlCanonical = canonical.attrib["href"]
			parsed = urlparse(self.urlCanonical)
			if(parsed.netloc == "answers.yahoo.com"):
				self.canonical = "EN"
			else:
				self.canonical = parsed.netloc[0:parsed.netloc.find(".")].upper()
		else:
			self.getXML()
			self.getCanonical()
		
	def getTitle(self):
		if hasattr(self, 'xml'):
			titulo = self.xml[0].xpath("//h1[contains(@class,'Mb-10')]|h1[contains(@class,'Fw-300')]|h1[contains(@class,'Fz-24')]")
			if(len(titulo)==1):
				titulo = titulo[0]
				self.title = titulo.text
			else:
				titulo = self.xml[0].xpath("//meta[@name='title']")[0]
				self.title = titulo.get("content")
		else:
			self.getXML()
			self.getTitle()

	def getBody(self):
		if hasattr(self, 'xml'):
			question = self.xml[0].xpath("//span[@class='D-n ya-q-full-text Ol-n']|//span[@class='ya-q-text']")
			if(len(question)>0):
				self.body = []
				for elemento in question:
					if(elemento.xpath("@class")[0] == 'D-n ya-q-full-text Ol-n'):
						self.body.pop()
					finalText = ""
					for text in elemento.itertext():
						finalText += text
					self.body.append(finalText)
			else:
				question = self.xml[0].xpath("//meta[@name='description']")[0]
				self.body = [question.get("content")]
		else:
			self.getXML()
			self.getBody()
			
	def getUser(self):
		if hasattr(self, 'xml'):
			profile = self.xml[0].xpath("//div[@id='yq-question-detail-profile-img']")
			if(len(profile)==1):
				profile = profile[0].getchildren()
				if(len(profile)==1):
					if(profile[0].tag=="div"):
						self.user = ("anonymous",None)
					else:
						profile = profile[0].getchildren()
						if(len(profile)==1):
							self.user = (profile[0].get("alt"),profile[0].get("data-id"))
						else:
							return None
				else:
					return None
			else:
				return None
		else:
			self.getXML()
			self.getUser()
			
	def getKeywords(self):
		if hasattr(self, 'xml'):
			keywords = self.xml[0].xpath("//meta[@name='keywords']")[0]
			self.keywords = []
			if(keywords>0):
				for elemento in keywords.get("content").split(","):
					self.keywords.append(elemento)
		else:
			self.getXML()
			self.getKeywords()
			
	def getAnswers(self, page = 1, filtered = False):
		if hasattr(self, 'xml'):
			if(not hasattr(self, 'answers')):
				self.answers = []
			if(page != 1):
				url = "%s&page=%i"%(self.url,page)
				self.getXML(_url = url, filtered = filtered)
			buffer = self.xml[page-1].xpath("//div[@data-ya-type='answer']|//li[@data-ya-type='answer']")
			for elemento in buffer:
				if(elemento.tag == "div"):
					if(not hasattr(self, 'bestAnswer')):
						self.bestAnswer = self.getAnswer(elemento)
				else:
					self.answers.append(self.getAnswer(elemento))
			if(page == 1):
				self.pageCount = 1
				pagination = self.xml[page-1].xpath("//div[@id='ya-qn-pagination']")
				if(len(pagination)>0):
					self.getAnswers(page = page + 1, filtered = filtered)
			else:
				pagination = self.xml[page-1].xpath("//div[@id='ya-qn-pagination']")
				self.pageCount = page
				if(len(pagination)>0):
					pages = pagination[0].xpath("//a[@class='Clr-bl']")
					if(str(pages[-1][0].text) == "next"):
						check = self.parseAtribs(pages[-1].get("data-ylk"))
						if(int(check["page"]) == page + 1):
							self.getAnswers(page = page + 1, filtered = filtered)
		else:
			self.getXML()
			self.getAnswers(filtered = filtered)
			
	def getAnswer(self,answer):
		texto = ""
		links = []
		imgs = []
		#Obtiene Usuario
		profile = answer.xpath("descendant::node()/img[contains(@class,'profileImage')]")
		if(len(profile) == 1):
			usuario = profile[0].get("alt")
			idUsuario = profile[0].get("data-id")
		else:
			usuario = "anonymous"
			idUsuario = None
		#Obtiene si el usuario es un contribuidor top
		topContributor = answer.xpath("descendant::node()//div[@class='Pt-15']/span[contains(@class, 'top-contributor')]")
		if(len(topContributor) == 0):
			topContributorBool = False
		else:
			topContributorBool = True
		#Obtiene Imagenes (si es que hay)
		images = answer.xpath("descendant::node()//div[@class='mm-img']")
		if(len(images) > 0):
			for img in images:
				buffer = img.xpath("descendant::node()/img")
				if(len(buffer)==1):
					imgs.append(buffer[0].get("src"))
		#Obtiene el id de la respuesta
		id = answer.get("data-ya-answer-id")
		#Obtiene texto de la respuesta
		respuesta = answer.xpath("descendant::node()/span[@class='ya-q-full-text']")
		if(len(respuesta) == 1):
			for linea in respuesta[0].itertext():
				texto += linea
			for link in respuesta[0].findall("a"):
				links.append(link.get("href"))
		#Obtiene el tiempo en formato Y!QA desde que fue escrita la respuesta
		time = answer.xpath("descendant::node()//span[@class='Clr-88 ya-localtime']")
		if(len(time) > 0):
			for t in time:
				relativeDate = t.text[3:-1]
				postDate = datetime.fromtimestamp(int(t.attrib["data-ts"]))
		else:
			relativeDate = None
		#Obtiene votos positivos
		thumbUp = answer.xpath("descendant::node()//div[@itemprop='upvoteCount']")
		if(len(thumbUp) == 1):
			thumbUp = int(thumbUp[0].text)
		else:
			thumbUp = None
		#Obtiene votos negativos
		thumbDown = answer.xpath("descendant::node()//div[@data-ya-type='thumbsDown']/div[@class='D-ib Mstart-23 count']")
		if(len(thumbDown) == 1):
			thumbDown = int(thumbDown[0].text)
		else:
			thumbDown = None
		return {"text":texto,"user":usuario,"idUser":idUsuario,"links":links,"id":id,"images":imgs,"relativeDate":relativeDate, "thumbUp":thumbUp, "thumbDown":thumbDown, "topContributor":topContributorBool, "postDate":postDate }
	
	def getAll(self, filtered = False):
		if not hasattr(self, 'xml'):
			self.getXML(filtered = filtered)
		self.getFollowers()
		self.getCategory()
		self.getTitle()
		self.getBody()
		self.getUser()
		self.getKeywords()
		self.getCanonical()
		self.getAnswers()
		self.makeXMLRaw()
		
	def makeXMLRaw(self):
		salida = E("root", qid = self.qid,user = self.user[0],idUser = str(self.user[1]),pages = str(self.pageCount),url = self.url,urlCanonical = self.urlCanonical,canonical = self.canonical, date = datetime.strftime(self.date,"%Y-%m-%d %H:%M:%S"), followers = str(self.followers), crawledDate = datetime.strftime(self.crawledDate,"%Y-%m-%d %H:%M:%S"))
		for idx, i in enumerate(self.xml):
			pagina = E("pagina", id = str(idx+1))
			pagina.append(i)
			salida.append(pagina)
		self.XMLRAW = salida


	def makeFinalXML(self, filtered = False):
		self.getAll(filtered = filtered)
		salida = E("question",qid = self.qid,user = self.user[0],idUser = str(self.user[1]),pages = str(self.pageCount),url = self.url,urlCanonical = self.urlCanonical,canonical = self.canonical, date = datetime.strftime(self.date,"%Y-%m-%d %H:%M:%S"), followers = str(self.followers), crawledDate = datetime.strftime(self.crawledDate,"%Y-%m-%d %H:%M:%S"))
		body = E("body",type = "container")
		for idx,elemento in enumerate(self.body):
			if(idx == 0):
				body.append(E("question",elemento, type = "body"))
			else:
				body.append(E("question", elemento, type = "update"))
		title = E("title",self.title)
		keywords = E("keywords")
		for elemento in self.keywords:
			keywords.append(E("keyword",elemento))
		categories = E("categories")
		for idx,elemento in enumerate(self.categories):
			categories.append(E("category",elemento[1], categoryId = str(elemento[0]), level = str(idx+1)))
		answers = E("answers")
		if(hasattr(self, 'bestAnswer')):
			bestAnswer = (E("answer", self.bestAnswer['text'], type = "bestAnswer", user= self.bestAnswer['user'], idUser= str(self.bestAnswer['idUser']), id= str(self.bestAnswer['id']), relativeDate= str(self.bestAnswer['relativeDate']), thumbUp= str(self.bestAnswer['thumbUp']), thumbDown= str(self.bestAnswer['thumbDown']), topContributor = str(self.bestAnswer['topContributor']), postDate = str(self.bestAnswer['postDate']) ))
			links = E("links")
			for link in self.bestAnswer["links"]:
				links.append(E("link",link))
			images = E("images")
			for image in self.bestAnswer["images"]:
				images.append(E("image",image))
			bestAnswer.append(links)
			bestAnswer.append(images)
			answers.append(bestAnswer)
		for elemento in self.answers:
			answer = (E("answer", elemento['text'], type = "answer", user= elemento['user'], idUser= str(elemento['idUser']), id= str(elemento['id']), relativeDate= str(elemento['relativeDate']), thumbUp= str(elemento['thumbUp']), thumbDown= str(elemento['thumbDown']), topContributor = str(elemento['topContributor']), postDate = str(elemento['postDate']) ))
			links = E("links")
			for link in elemento["links"]:
				links.append(E("link",link))
			images = E("images")
			for image in elemento["images"]:
				images.append(E("image",image))
			answer.append(links)
			answer.append(images)
			answers.append(answer)
		salida.append(title)
		salida.append(body)
		salida.append(keywords)
		salida.append(categories)
		salida.append(answers)
		self.finalXML = salida
		self.finalXMLString = etree.tostring(salida,pretty_print=True, xml_declaration=True, encoding='UTF-8')
		self.finalXMLJSON = xml2json.xml_to_json(self.finalXML)
		self.finalXMLRAWString = etree.tostring(self.XMLRAW,pretty_print=True, xml_declaration=True, encoding='UTF-8')
		
