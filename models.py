from google.appengine.ext import db

class AlertChannel(db.Model):
  """Representing an alert channel."""
  name = db.StringProperty(required=True)
  description = db.TextProperty()
  creator = db.UserProperty()
  target_jids = db.ListProperty(str)
  # try just keeping a list of jids who want notification.

#class AlertTarget(db.Model):
#  """a known user. auto populated when a user subscribes to a channel."""
#  user = db.UserProperty()
#  enabled = db.BooleanProperty()
