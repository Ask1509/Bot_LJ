#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from bot import LJbot

if __name__ == "__main__":
	try:
		postUrl = "http://jenyay-test.livejournal.com/21935.html"

		login = u"USERNAME"
		password = u"PASSWORD"

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
