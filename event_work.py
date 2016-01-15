import db_events
import event_merge
import event_mapping


def map_events(events):
	"""
		Map sections in text to events
	"""
	import event_sections

	return reduce(event_mapping.map_event_section, event_sections.sections, events)


def make_event_authors(events):
	"""
		Make new author names like 'A', 'B', ... , '1A', and so on.
	"""
	authors = {}
	for pad, revs, event in events:
		author = event[u'meta'][u'author']
		if author not in authors:
			i = len(authors)
			m = ord('Z') - ord('A') + 1
			n = i / m
			l = chr(ord('A') + i % m)

			authors[author] = "%d%s" % (n, l) if n else l

	return authors


def map_event_authors(events, authors):
	"""
		Map authors to events
	"""
	for event in events:
		event.author = authors[event.author]
		yield event


def export_events(merge_events):
	"""
		Convert events for futher export into file / db
	"""
	import json

	def ts2s(timestamp):
		"""
			Convert timestamp (in seconds) into printable datetime format.
		"""
		import time
		return time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(timestamp))

	for revision, merge_event in enumerate(merge_events):
		event = merge_event.events[0]
		last_event = merge_event.events[-1]

		p_start, p_end, p_text = merge_event.positive_changes
		n_start, n_end, n_text = merge_event.negative_changes

		author = event.author
		case = event.case or ""
		section = event.section or ""
		start_revision = event.revision
		end_revision = last_event.revision
		timestamp = ts2s(event.timestamp)

		changeset = json.dumps({
			 # "revisions": [event.revision for event in merge_event.events],

			 "positive": p_text.encode("utf8"),
			 "positive_start": p_start,
			 "positive_length": p_end - p_start,

			 "negative": n_text.encode("utf8"),
			 "negative_start": n_start,
			 "negative_length": n_end - n_start
		})

		yield revision + 1, author, case, section, end_revision, timestamp, changeset


def csv_export(header, rows, filename):
	"""
		Export rows into csv file 'filename' with header.
	"""
	import csv

	with open(filename, "w") as csv_file:
		writer = csv.writer(csv_file, delimiter = ";")
		writer.writerows([header])
		writer.writerows(rows)



def process_events(events, authors, threshold):
	events = map_events(events)
	events = event_merge.make_events(events)
	events = map_event_authors(events, authors)

	merge_events = (event_merge.MergeEvent([event]) for event in events)
	merge_events = event_merge.merge_events(merge_events, timestamp_threshold)

	return merge_events


def print_events(merge_events):
	import event_html

	merge_events = list(merge_events)

	for merge_event in merge_events:
		end_event = merge_event.events[-1]
		events = event_html.order_events(merge_events)
		events = event_html.sentinel_events(events, end_event)
		text = event_html.build_event_text(events)
		yield event_html.format_event_text(text, merge_event), end_event.revision


def html_export(texts, filename):
	for text, n in texts:
		with open(filename % n, "w") as html_file:
			html_file.write(text.encode("ascii", "xmlcharrefreplace"))	


if __name__ == "__main__":
	import sys
	pad = sys.argv[1]

	print "Processing %s pad" % pad
	timestamp_threshold = 60

	events = db_events.load_events(pad)
	authors = make_event_authors(db_events.load_events(pad))
	merge_events = process_events(events, authors, timestamp_threshold)

	merge_events = list(merge_events)

	# csv_header = ["nr", "user", "case", "eventtext", "startrevision", "endrevision", "starttime", "changeset"]
	csv_header = ["nr", "user", "case", "eventtext", "endrevision", "starttime", "changeset"]
	csv_export(csv_header, export_events(merge_events), "%s_merge_events.csv" % pad)

	# html_export(print_events(merge_events), "%s_%%d.html" % pad)
	print "Processing done."
