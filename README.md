# pyrax-ping-watcher

Service for monitoring rackspace servers, and restarting those that appear inaccessible.

We've been having issues with tmpnb servers going down (https://try.jupyter.org) in a pretty hard manner.
The main symptom of this is that ping checks indicate that the server is inaccessible.
Rebooting the server always fixes the problem.

The answer: pyrax-ping-watcher.

- periodically checks status of ping checks via rackspace API
- if a server is found to be down, reboot it

That's about it.
