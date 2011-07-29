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
      if not sub.user:
        logging.warning("odd. sub.user has no value?")
        continue
      if xmpp.get_presence(sub.user.email()):
        status_code = xmpp.send_message(sub.user.email(), message)
        if status_code != xmpp.NO_ERROR:
          logging.error("Did not send message!")
          logging.error(status_code)
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
    if not users.get_current_user():
      self.redirect(users.create_login_url(self.request.uri))
      return
    channel = self.request.get('channel')
    if not channel:
      self.response.set_status(400, "User Error")
      self.response.out.write("you must specify a channel name.")
      return
    if self.request.path == '/channel/notify':
      logging.info("attempting to notify users.")
      self.notifyChannel(channel, 
                         self.formatChannelMessage(channel, self.request.get('message', None)))
      self.response.set_status(200, "Ok")
      self.response.out.write("notification sent.")

    elif self.request.path == '/channel':
      #create new channel.
      chan = models.Channel(name=self.request.get('name'))
      chan.description = self.request.get('description', '')
      chan.creator = users.get_current_user()
      chan.put()
      self.response.set_status(200, "channel created.")
      self.response.out.write('channel created.')
      if chan.creator:
        # auto-subscribe the creator
        sub = models.ChannelSubscription(parent=chan.key())
        sub.user = chan.creator
        sub.enabled = True
        sub.put()
        self.response.out.write(' You have been subscribed.')
    else:
      self.response.set_status(400, "user error")
      self.response.out.write("improper url path.")


class SubscribeHandler(webapp.RequestHandler):
  """Subscription changes."""
  def get(self):
    if not users.get_current_user():
      self.redirect(users.create_login_url(self.request.uri))
      return
    
    if not self.request.get('channel'):
      self.response.set_status(400, "WHUT??")
      return

    current_user = users.get_current_user()
    chanobj = models.Channel.gql("WHERE name = :1", self.request.get('channel')).get()
    if not chanobj:
      self.response.set_status(400, "WHUT??")
      return
    sub = models.ChannelSubscription.gql("WHERE ANCESTOR IS :1 AND user = :2", chanobj.key(), current_user).get()
    if sub and sub.user:
      xmpp.send_invite(sub.user.email())
      self.response.set_status(200, "ok")
      self.response.out.write('already subscribed.')
      return
    else:
      sub = models.ChannelSubscription(
          user=current_user,
          enabled=True,
          parent=chanobj.key())
      sub.put()
      xmpp.send_invite(sub.user.email())
      self.response.set_status(200, "ok")
      self.response.out.write('invitation sent.')
    

class MainHandler(webapp.RequestHandler):
    def get(self):
        self.redirect('/channels')


def main():
    application = webapp.WSGIApplication([('/', MainHandler),
                                          ('/subscribe', SubscribeHandler),
                                          ('/channel.*', ChannelHandler),
                                         ], debug=True)
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()
