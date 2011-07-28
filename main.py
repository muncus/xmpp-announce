#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
from google.appengine.api import users
from google.appengine.api import xmpp

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp import util

import logging
import models

class ChannelHandler(webapp.RequestHandler):
  """Show and edit channel subscriptions."""

  def notifyChannel(self, channel, message):
    """Send notification out to all subscribed users."""
    chanobj = models.Channel.gql("WHERE name = :1", channel).get()
    subscriptions = models.ChannelSubscription.gql("WHERE ANCESTOR IS :1", chanobj.key())
    for sub in subscriptions:
      if xmpp.get_presence(sub.user.email()):
        xmpp.send_message(sub.user.email(), message)
      else:
        logging.info("user not online: %s" % sub.user.email())

  def formatChannelMessage(self, channel, message=None):
    """Formats the given message as appropriate for announcement."""
    if not message:
      message = "%s time!" % channel
    if users.get_current_user():
      return "%s says: %s" % (users.get_current_user(), message)

  def get(self):
    logging.info("in channel handler.")
    channel = self.request.get('channel')
    if self.request.path == '/channel/notify':
      if not channel:
        self.response.set_status(400, "User Error")
        self.response.out.write("you must specify a channel name.")
        return
      logging.info("attempting to notify users.")
      self.notifyChannel(channel, 
                         self.formatChannelMessage(channel, self.request.get('message', None)))
      self.response.set_status(200, "Ok")
      self.response.out.write("notification sent.")
      return
    if self.request.path == '/channel':
      #adding a new channel.
      self.response.out.write(template.render('templates/create_channel.html', None))
      return
    if self.request.path == '/channels':
      chans = models.Channel.all()
      self.response.out.write(template.render('templates/channel_list.html', {
          'channels': chans}
          ))
      return
    else:
      self.response.set_status(400, "User Error")
      self.response.out.write("huh?")

  def post(self):
    #create new channel.
    chan = models.Channel(name=self.request.get('name'))
    chan.description = self.request.get('description', '')
    chan.creator = users.get_current_user()
    chan.put()
    # auto-subscribe the creator
    sub = models.ChannelSubscription(parent=chan.key())
    sub.user = chan.creator
    sub.enabled = True
    sub.put()
    self.response.set_status(200, "channel created.")
    self.response.out.write('channel created.')


class SubscribeHandler(webapp.RequestHandler):
  """Subscription changes."""
  def get(self):
    if not self.request.get('channel'):
      self.response.set_status(400, "WHUT??")
    chanobj = models.Channel.gql("WHERE name = :1", self.request.get('channel')).get()
    sub = models.ChannelSubscription.get_or_insert(
        user=users.get_current_user(),
        enabled=True,
        parent=chanobj.key())
    self.response.set_status(200, "ok")
    self.response.out.write('subscribed.')
    

class MainHandler(webapp.RequestHandler):
    def get(self):
        self.response.out.write('Hello world!')

    def listChannels(self):
      pass


def main():
    application = webapp.WSGIApplication([('/', MainHandler),
                                          ('/subscribe', SubscribeHandler),
                                          ('/channel.*', ChannelHandler),
                                         ], debug=True)
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()
