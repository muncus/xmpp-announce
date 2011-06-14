# largely based on sample code from appengine docs.

import logging, email
from google.appengine.ext import webapp 
from google.appengine.ext.webapp.mail_handlers import InboundMailHandler 
from google.appengine.ext.webapp.util import run_wsgi_app

class LogSenderHandler(InboundMailHandler):
    def receive(self, mail_message):
            logging.info("Received a message from: " + mail_message.sender)


application = webapp.WSGIApplication([LogSenderHandler.mapping()], debug=True)

def main():
    run_wsgi_app(application)

if __name__ == '__main__':
    main()
