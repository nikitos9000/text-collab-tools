def order_events(merge_events):
	import heapq
	event_heap = []

	last_revision = None
	for merge_event in merge_events:
		for event in merge_event.events:
			heapq.heappush(event_heap, (event.revision, event))

		while event_heap:
			revision, event = event_heap[0]
			if last_revision and revision != last_revision + 1:
				break

			yield event

			last_revision = revision
			heapq.heappop(event_heap)


def sentinel_events(events, sentinel_event):
	for event in events:
		yield event

		if event == sentinel_event:
			break


def build_event_text(events, text = "\n"):
	import text_events

	for event in events:
		event_data = text_events.text_apply_event(text, event.changeset_data)
		text, event_changes, event_new_changes = event_data

	return text


def format_text_sections(text):
	import event_html_template as template

	import re
	import event_sections

	def default_section(pattern, header, children = []):
		return pattern, children

	cases, sections = event_sections.sections

	stack = list(sections)

	while stack:
		section = stack.pop()
		pattern, children = default_section(*section)
		stack.extend(children)

		text = re.sub(pattern, template.section_template % "\g<0>", text)

	return text


def format_event_text(text, merge_event):
	import event_html_template as template

	result_text = ""

	p_start, p_end, p_text = merge_event.positive_changes 
	n_start, n_end, n_text = merge_event.negative_changes

	positive_text = p_text and template.positive_changes_template % p_text 
	negative_text = n_text and template.negative_changes_template % n_text

	if p_start < n_start:
		result_text += text[:p_start]
		result_text += positive_text
		result_text += text[p_end:max(p_end, n_start)]
		result_text += negative_text
		result_text += text[max(p_end, n_start):]
	else:
		result_text += text[:n_start]
		result_text += negative_text
		result_text += text[n_start:p_start]
		result_text += positive_text
		result_text += text[p_end:]

	for text_replace, text_template in template.text_templates:
		result_text = result_text.replace(text_replace, text_template)

	result_text = format_text_sections(result_text)
	return template.content_template % result_text
