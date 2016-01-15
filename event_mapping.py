import text_events
import db_events

def make_sections_mapping(patterns, text):
	"""
		Recursively divide text into sections and subsections, 
		which are provided by patterns.
	"""
	def default_pattern_data(pattern, header, children = []):
		return pattern, header, children

	source_section_headers = []

	for pattern_data in patterns:
		pattern, header, children = default_pattern_data(*pattern_data)

		for start, end, header in text_events.text_bound_mapping(text, pattern, header):
			source_section_headers.append((start, end, header, children))

	section_headers = []

	for s_start, s_end, s_header, s_children in source_section_headers:
		for e_start, e_end, e_header, e_children in source_section_headers:
			if s_header != e_header and min(s_end, e_end) - max(s_start, e_start) > 0:
				raise Exception("Headers can't overlap: %s and %s" % (s_header, e_header))
		else:
			section_headers.append((s_start, s_end, s_header, s_children))

	section_headers.sort()

	last_end = 0
	last_header = None
	last_children = None

	sections = []

	for start, end, header, children in section_headers:
		if last_header is not None and start > last_end:
			sections.append((last_end, start, last_header, last_children))

		last_end = end
		last_header = header
		last_children = children

	if last_header is not None and len(text) > last_end:
		sections.append((last_end, len(text), last_header, last_children))

	for start, end, header, children in sections:
		yield start, end, (header,)

		for c_start, c_end, c_headers in make_sections_mapping(children, text[start:end]):
			yield start + c_start, start + c_end, (header,) + c_headers


def map_event_section(events, patterns, text = "\n"):
	"""
		Map each event to a section in the text. Sections are provided by patterns.
	"""
	def make_event_data(pad, revs, event, args = ()):
		return pad, revs, event, args

	for event_data in events:
		pad, revs, event, data = make_event_data(*event_data)
		event_changeset = text_events.parse_event_changeset(event[u'changeset'])

		text, changes, new_changes = text_events.text_apply_event(text, event_changeset)

		range_sections = []

		for start, end, section in make_sections_mapping(patterns, text):
			for change_start, change_end in new_changes:
				if start <= change_start < end or start < change_end <= end:
					if section and (start, end, section) not in range_sections:
						range_sections.append((start, end, section))

		sections = []

		for s_start, s_end, s_section in range_sections:
			for e_start, e_end, e_section in range_sections:
				if s_section != e_section and s_start <= e_start and e_end <= s_end:
					if e_end - e_start < s_end - s_start:
						break
			else:
				sections.append(s_section[-1]) # get only last part

		(section,) = sections if len(sections) == 1 else (None,)

		yield pad, revs, event, data + (section,)
