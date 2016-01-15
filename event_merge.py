import text_events

class Event(object):
	def __init__(self, pad, revision, timestamp, author, changeset, changeset_data):
		self.pad = pad
		self.revision = revision
		self.timestamp = timestamp
		self.author = author
		self.changeset = changeset
		self.changeset_data = changeset_data

	def __repr__(self):
		return str(self.__dict__)


class MergeEvent(object):
	def __init__(self, events):
		self.events = events

	def __repr__(self):
		return str(self.__dict__)


def make_events(events):
	"""
		Make event objects from the raw event data. Event gets it own changeset,
		case and section mappings, bindings with texts before and after the event.

		Changeset is a list of operations parsed from event changeset text, timestamp is converted to seconds.
	"""
	for pad, revision, data, (case, section) in events:
		timestamp = data[u'meta'][u'timestamp'] / 1000
		author = data[u'meta'][u'author']
		changeset = data[u'changeset']

		changeset_data = text_events.parse_event_changeset(changeset)

		event = Event(pad, revision, timestamp, author, changeset, changeset_data)
		event.case = case
		event.section = section

		yield event


def merge_events(events, threshold, text = "\n"):
	"""
		Merge events with the same author and if they overlap or have common bounds. 
		Events may even not be subsequent, but they shouldn't depend on alternating events happened
		in the middle.

		"event_queue" is filled while events are in time window (threshold), 
		then it is processed by taking the expanding event subsequence and trying to get a changeset from it.
		The longest event subsequence with correct independent changeset is merged into one event.
	"""

	events = iter(events)
	event_queue = []

	next_event = next(events, None)

	while next_event or event_queue:

		while next_event:
			if event_queue:
				base_merge_event, base_include = event_queue[0]

				timestamp = base_merge_event.events[0].timestamp
				new_timestamp = next_event.events[-1].timestamp

				if new_timestamp - timestamp >= threshold:
					break

			event_queue.append((next_event, True))
			next_event = next(events, None)

		event_author = None

		check_queue = []
		check_event_queue = []

		max_event_queue = []
		max_event_positive_change = None
		max_event_negative_change = None

		for merge_event, include in event_queue:
			if event_author is None:
				event_author = merge_event.events[0].author

			if merge_event.events[0].author == event_author:
				check_event_queue.append(merge_event)

			check_queue_length = 0
			for event in merge_event.events:
				check_include = include and event.author == event_author
				check_queue.append((event.changeset_data, check_include))

				if check_include:
					check_queue_length = len(check_queue)

			if not check_queue_length:
				continue

			event_changes = text_events.text_make_changes_events(text, check_queue[:check_queue_length])

			if event_changes:
				max_event_queue = list(check_event_queue)
				max_event_positive_change, max_event_negative_change = event_changes

		new_event_index = 0
		for event_index, (merge_event, include) in enumerate(event_queue):
			include &= merge_event not in max_event_queue

			if new_event_index or include:
				event_queue[new_event_index] = merge_event, include
				new_event_index += 1
			else:
				for event in merge_event.events:
					event_data = text_events.text_apply_event(text, event.changeset_data)
					text, event_changes, event_new_changes = event_data

		del event_queue[new_event_index:]

		if max_event_queue:
			merge_event = MergeEvent([event for merge_event in max_event_queue for event in merge_event.events])
			merge_event.positive_changes = max_event_positive_change
			merge_event.negative_changes = max_event_negative_change
			merge_event.merge_count = len(max_event_queue)
			yield merge_event
