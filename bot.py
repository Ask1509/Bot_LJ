#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
Бот для ЖЖ.
Версия 1.2

История версий:

1.2
* Изменения, связанные с изменениями на сервере ЖЖ

1.1
* Добавил возможность отвечать на комментарии
* Почистил код

1.0
* Кажется, бот работает.
"""

import urllib
import urllib2
import hashlib
import re

class ServerError (BaseException):
	pass

class AuthError (BaseException):
	pass

class ParseError (BaseException):
	pass


class LJbot (object):
	def __init__ (self, login, password):
		self.login = login
		self.password = password

		self.flatServerUrl = u"http://www.livejournal.com/interface/flat"

		# Используемые регулярные выражения
		self.authFormRe = re.compile ("(\\\\)?\"lj_form_auth(\\\\)?\" value=(\\\\)?\"(?P<auth>.*?)(\\\\)?\"", re.IGNORECASE| re.DOTALL | re.MULTILINE)

		self.cookie = self.loginAsUser (login, password)


	def parseResponse (self, textResponse):
		"""
		Создать словарь по данным из ответа
		"""
		elements = textResponse.split()
		names = elements[::2]
		values = elements[1::2]

		result = dict(zip (names, values) )

		return result


	def getChallenge (self):
		"""
		Получить оклик для авторизации
		"""
		dataDict = {
				"mode": "getchallenge"
				}

		data = urllib.urlencode (dataDict)
		
		request = urllib2.Request (self.flatServerUrl, data)

		fp = urllib2.urlopen (request)
		text = fp.read ()
		fp.close()

		response = self.parseResponse (text)
		return response


	def getAuthResponse (self, password, challenge):
		hpass = hashlib.md5(password).hexdigest()
		response = hashlib.md5 (challenge + hpass).hexdigest()
		return response


	def loginAsUser (self, login, password):
		"""
		Авторизация как посетитель сайта
		"""
		challenge_resp = self.getChallenge()

		if challenge_resp["success"] != "OK":
			raise ServerError

		# Получим оклик
		challenge = challenge_resp["challenge"]

		# Получим ответ на оклик для авторизации
		auth_response = self.getAuthResponse (password, challenge)

		authData = urllib.urlencode ({
				"chal": challenge,
				"response": auth_response,
				"user": login
				})

		server = "http://www.livejournal.com/login.bml"

		cookieHandler = urllib2.HTTPCookieProcessor ()
		opener = urllib2.build_opener(cookieHandler)
		

		request = urllib2.Request (server, authData)

		fp = opener.open (request)
		fp.close()

		if len (cookieHandler.cookiejar) < 2:
			raise AuthError

		return cookieHandler.cookiejar


	def openUrlWithCookie (self, url, cookiejar):
		cookieHandler = urllib2.HTTPCookieProcessor (cookiejar)
		opener = urllib2.build_opener(cookieHandler)	

		request = urllib2.Request (url)

		fp = opener.open (request)
		text = fp.read()
		fp.close()

		return text


	def loginClear (self, login, password):
		"""
		Авторизация методом clear (лучше не пользоваться)
		"""
		dataDict = {
				"mode": "login",
				"auth_method": "clear",
				"user": login,
				"password": password
				}

		data = urllib.urlencode (dataDict)
		
		request = urllib2.Request (self.flatServerUrl, data)

		fp = urllib2.urlopen (request)
		text = fp.read ()
		info = fp.info()
		fp.close()
	

	def parseUrl (self, url):
		"""
		Из адреса вычленить имя журнала и номер поста.
		Возвращает кортеж (username, id), например, для http://community.livejournal.com/ljournalist/314088.html: (ljournalist, 314088)
		"""
		# Найдем номер поста и имя пользователя
		if url.startswith ("http://community.livejournal.com"):
			# Сообщество
			urlRe = re.compile ("http://community.livejournal.com/(?P<name>.*)/(?P<id>\d+)\.html", re.IGNORECASE)
		else:
			urlRe = re.compile ("http://(?P<name>.*).livejournal.com/(?P<id>\d+)\.html", re.IGNORECASE)

		url_match = urlRe.search (url)

		if url_match == None:
			raise ParseError

		return url_match.group ("name"), url_match.group ("id")




	def postComment (self, url, message, subject="", replyto=0):
		urlServer = "http://www.livejournal.com/talkpost_do.bml"

		# Надо узнать:
		# + lj_form_auth
		# + journal
		# + itemid
		# + cookieuser

		text = self.openUrlWithCookie (url, self.cookie)

		# lj_form_auth
		auth_match = self.authFormRe.search (text)

		if not auth_match:
			raise ParseError

		lj_form_auth = auth_match.group ("auth")

		cookieuser = self.login.replace ("-", "_")

		journal, itemid = self.parseUrl (url)

		journal = journal.replace ("-", "_")

		params = {
			"usertype": "cookieuser",
			"subject": subject.encode ("utf-8"),
			"body": message.encode ("utf-8"),
			"lj_form_auth": lj_form_auth,
			"cookieuser": cookieuser,
			"journal": journal,
			"itemid": itemid,
			"parenttalkid": replyto
		}

		cookieHandler = urllib2.HTTPCookieProcessor (self.cookie)
		opener = urllib2.build_opener(cookieHandler)
		
		params_encoded = urllib.urlencode (params)
		request = urllib2.Request (urlServer, params_encoded)

		fp = opener.open (request)
		result = fp.read()
		fp.close()


if __name__ == "__main__":
	try:
		postUrl = "http://jenyay-test.livejournal.com/21935.html"

		login = u""
		password = u""

		bot = LJbot (login, password)

		subj = unicode ("Превед", "utf-8")
		message = unicode ("Превед, ботег!!!", "utf-8")
		
		bot.postComment (postUrl, message, subject = subj, replyto = 0)

	except ServerError:
		print "Server Error"
	except AuthError:
		print "Auth Error"
	except ParseError:
		print "Parse Error"
