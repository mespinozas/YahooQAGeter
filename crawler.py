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
		if(self.checkQID(qid)):
			self.url = "https://answers.yahoo.com/question/index?qid=%s"%(qid)
			self.qid = qid
			self.proxy = proxy
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
			
	def getSourceCode(self, url):
		#si proxy es distinto de None, tiene la forma
		#{"protocolo":"<protocolo>", "urlProxy":"<direccion del proxy: user:pass@url>", "puerto":"<puerto del proxy>"}
		#Ejemplo {"protocolo":"https", "urlProxy":"52.53.254.181", "puerto":"8083"}
		if(self.proxy is None):
			opener = urllib2.urlopen(url)
			data = opener.read()
		else:
			proxy = urllib2.ProxyHandler({self.proxy["protocolo"]: "{}:{}".format(self.proxy["urlProxy"], self.proxy["puerto"])})
			opener = urllib2.build_opener(proxy)
			urllib2.install_opener(opener)
			data = urllib2.urlopen(url).read()
		return data
	
	def getXML(self, filtered = False):
		try:
			datos = self.getSourceCode(self.url)
		except:
			datos = None
		if(datos == None):
			self.xml = None
		else:
			if(filtered):
				self.xml = etree.HTML(cleanStringToLXML(datos))
			else:
				self.xml = etree.HTML(datos)
			
	def parseAtribs(self, atributos):
		salida = {}
		for elemento in atributos.split(";"):
			salida[elemento.split(":")[0]] = elemento.split(":")[1]
		return salida
			
	def getCategory(self):
		if hasattr(self, 'xml'):
			categorias = []
			categoria = self.xml.xpath("//div[@id='brdCrb']")
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

#Canonical se refiere al idioma de la pregunta y en que lenguaje de yahoo se encuentra
	def getCanonical(self):
		if hasattr(self, 'xml'):
			canonical = self.xml.xpath("//link[@rel='canonical']")
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
			titulo = self.xml.xpath("//h1[contains(@class,'Mb-10')]|h1[contains(@class,'Fw-300')]|h1[contains(@class,'Fz-24')]")
			if(len(titulo)==1):
				titulo = titulo[0]
				self.title = titulo.text
			else:
				titulo = self.xml.xpath("//meta[@name='title']")[0]
				self.title = titulo.get("content")
		else:
			self.getXML()
			self.getTitle()

	def getBody(self):
		if hasattr(self, 'xml'):
			question = self.xml.xpath("//span[@class='D-n ya-q-full-text Ol-n']|//span[@class='ya-q-text']")
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
				question = self.xml.xpath("//meta[@name='description']")[0]
				self.body = [question.get("content")]
		else:
			self.getXML()
			self.getBody()
			
	def getUser(self):
		if hasattr(self, 'xml'):
			profile = self.xml.xpath("//div[@id='yq-question-detail-profile-img']")
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
			keywords = self.xml.xpath("//meta[@name='keywords']")[0]
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
				try:
					newXML = self.getSourceCode(url)
				except:
					newXML = "<div></div>"
				if(filtered):
					newXML = etree.HTML(cleanStringToLXML(newXML))
				else:
					newXML = etree.HTML(newXML)
				buffer = newXML.xpath("//div[@data-ya-type='answer']|//li[@data-ya-type='answer']")
			else:
				buffer = self.xml.xpath("//div[@data-ya-type='answer']|//li[@data-ya-type='answer']")
			for elemento in buffer:
				if(elemento.tag == "div"):
					if(not hasattr(self, 'bestAnswer')):
						self.bestAnswer = self.getAnswer(elemento)
				else:
					self.answers.append(self.getAnswer(elemento))
			if(page == 1):
				self.pageCount = 1
				pagination = self.xml.xpath("//div[@id='ya-qn-pagination']")
				if(len(pagination)>0):
					self.getAnswers(page = page + 1, filtered = filtered)
			else:
				pagination = newXML.xpath("//div[@id='ya-qn-pagination']")
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
		profile = answer.xpath("descendant::node()/img[contains(@class,'profileImage')]")
		if(len(profile)==1):
			usuario = profile[0].get("alt")
			idUsuario = profile[0].get("data-id")
		else:
			usuario = "anonymous"
			idUsuario = None
		images = answer.xpath("descendant::node()//div[@class='mm-img']")
		if(len(images)>0):
			for img in images:
				buffer = img.xpath("descendant::node()/img")
				if(len(buffer)==1):
					imgs.append(buffer[0].get("src"))
		id = answer.get("data-ya-answer-id")
		respuesta = answer.xpath("descendant::node()/span[@class='ya-q-full-text']")
		if(len(respuesta)==1):
			for linea in respuesta[0].itertext():
				texto += linea
			for link in respuesta[0].findall("a"):
				links.append(link.get("href"))
		return {"text":texto,"user":usuario,"idUser":idUsuario,"links":links,"id":id,"images":imgs}
	
	
	def getAll(self, filtered = False):
		if hasattr(self, 'xml'):
			self.getXML(filtered = filtered)
		self.getCategory()
		self.getTitle()
		self.getBody()
		self.getUser()
		self.getKeywords()
		self.getAnswers()
		self.getCanonical()
		
	def makeFinalXML(self, filtered = False):
		self.getAll(filtered = filtered)
		salida = E("question",qid = self.qid,user = self.user[0],idUser = str(self.user[1]),pages = str(self.pageCount),url = self.url,urlCanonical = self.urlCanonical,canonical = self.canonical,date = datetime.strftime(self.date,"%Y-%m-%d %H:%M:%S"))
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
			bestAnswer = (E("answer", self.bestAnswer['text'], type = "bestAnswer", user= self.bestAnswer['user'], idUser= str(self.bestAnswer['idUser']), id= str(self.bestAnswer['id'])))
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
			answer = (E("answer", elemento['text'], type = "answer", user= elemento['user'], idUser= str(elemento['idUser']), id= str(elemento['id'])))
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
		
