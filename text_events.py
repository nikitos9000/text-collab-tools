import re

def text_bound_mapping(text, pattern, replace):
	"""
		Divides text into sections bounded by pattern.
	"""
	for match in re.finditer(pattern, text):
		if replace is not None:
			header = re.sub(pattern, replace, match.group())
		else:
			header = match.group()

		yield match.start(), match.end(), header


def text_make_changes_events(text, changesets):
	"""
		Calculates changes (pair of new and removed charaters) on the list of changesets.
	"""

	# newly added characters
	positive_changes = 0, 0, ""

	# deleted characters
	negative_changes = 0, 0, ""

	for changeset, include in changesets:
		length, new_length, operations, bank = changeset

		if length != len(text):
			raise Exception("Fail: length != len(text): %d != %d" % (length, len(text)))

		text_index = 0
		bank_index = 0

		final_text = ""

		final_length = 0

		s_text_index = 0
		s_bank_index = 0
		s_final_length = 0

		sign_operations = []
		sign_positive_keep = False
		for attributes, newlines, (characters, sign) in operations:
			if not sign and not sign_positive_keep:
				sign_text = text[s_text_index:s_text_index + characters]
				sign_operations.append((0, characters, sign_text))

				s_final_length += characters
				s_text_index += characters

			elif sign >= 0:
				if sign > 0:
					sign_text = bank[s_bank_index:s_bank_index + characters]
					sign_operations.append((+1, characters, sign_text))

					s_bank_index += characters
				else: # split non-starting keep into deletion and addition
					sign_text = text[s_text_index:s_text_index + characters]
					sign_operations.append((-1, characters, sign_text))
					sign_operations.append((+1, characters, sign_text))

					s_text_index += characters

				sign_positive_keep = True
				s_final_length += characters
			else:
				sign_text = text[s_text_index:s_text_index + characters]
				sign_operations.append((-1, characters, sign_text))

				sign_positive_keep = True
				s_text_index += characters

		# order signs by [0, -1, +1] (starting keeps, deletions, additions)
		sign_operations.sort(key = lambda (sign, characters, text): abs(sign) * 2 + sign)

		for sign, characters, sign_text in sign_operations:
			if not sign:
				final_text += sign_text

				final_length += characters
				text_index += characters
			elif sign > 0:
				i_text = sign_text
				final_text += sign_text
				final_length += characters

				i_start = final_length - characters
				i_length = characters

				p_start, p_end, p_text = positive_changes
				n_start, n_end, n_text = negative_changes

				if not p_text:
					if include:
						positive_changes = i_start, i_start + i_length, i_text
				elif p_start <= i_start <= p_end:
					if include:
						positive_changes = p_start, p_end + i_length, p_text[:i_start - p_start] + i_text + p_text[i_start - p_start:]
					else: # We can't modify events from other users
						return None

				elif not include:
					if i_start < p_start:
						positive_changes = p_start + i_length, p_end + i_length, p_text

				elif include: # Event included but isn't mergeable
					return None

				if n_text and n_start >= i_start:
					negative_changes = n_start + i_length, n_end + i_length, n_text

			else:
				text_index += characters

				p_start, p_end, p_text = positive_changes

				r_start = text_index - characters
				r_length = characters
				r_text = sign_text

				if p_text:
					if p_start - r_length <= r_start <= p_end:
						if not include: # We can't modify events from other users
							return None

						if p_start < r_start and r_start + r_length <= p_end:
							positive_changes = p_start, p_end - r_length, p_text[:r_start - p_start] + p_text[r_start - p_start + r_length:]
							r_text = ""
							r_length = len(r_text)
						else:
							negative_text = text[r_start:p_start] + text[p_end:r_start + r_length]

							if r_start <= p_start:
								positive_changes = r_start, p_end - r_length, p_text[r_start - p_start + r_length:]
								r_text = r_text[:p_start - r_start] + r_text[p_end - r_start:]
								r_length = len(r_text)
							else:
								positive_changes = p_start, r_start, p_text[:r_start - p_start]
								r_text = r_text[p_end - r_start:]
								r_length = len(r_text)

					elif not include:
						if p_start > r_start:
							positive_changes = p_start - r_length, p_end - r_length, p_text

					elif include: # Event included but isn't mergeable
						return None

				n_start, n_end, n_text = negative_changes

				if not n_text:
					if include:
						negative_changes = r_start, r_start + r_length, r_text
				else:
					if include:
						r_center = max(n_start - r_start, 0)
						negative_changes = r_start, r_start + r_length + n_end - n_start, r_text[:r_center] + n_text + r_text[r_center:]

					elif r_start <= n_start <= r_start + r_length:
						return None
					elif r_start <= n_start:
						negative_changes = n_start - r_length, n_end - r_length, n_text

		text = final_text + text[text_index:]

		if new_length != len(text):
			raise Exception("Fail: new_length != len(text): %d != %d" % (new_length, len(text)))

	return positive_changes, negative_changes


def text_apply_event(text, changeset):
	"""
		Apply changeset to the given text, obtaining the next text revision.
	"""
	length, new_length, operations, bank = changeset

	if length != len(text):
		raise Exception("Fail: length != len(text): %d != %d" % (length, len(text)))

	text_index = 0
	bank_index = 0

	final_text = ""

	# changes to source text
	changes = []

	# changes to final text
	new_changes = []

	for attributes, newlines, (characters, sign) in operations:
		if not sign:
			final_text += text[text_index:text_index + characters]
			text_index += characters
		elif sign > 0:
			final_text += bank[bank_index:bank_index + characters]
			bank_index += characters

			changes.append((text_index, text_index))
			new_changes.append((len(final_text) - characters, len(final_text)))
		else:
			text_index += characters

			changes.append((text_index - characters, text_index))
			new_changes.append((len(final_text), len(final_text)))

	final_text += text[text_index:]

	if new_length != len(final_text):
		raise Exception("Fail: new_length != len(final_text): %d != %d" % (new_length, len(final_text)))

	return final_text, changes, new_changes


def parse_event_changeset(changeset):
	"""
		Parse changeset into a list of operations and other changes information.
	"""
	length_token, new_length_token, operation_tokens, bank = tokenize_event_changeset(changeset)

	length = int(length_token[1:], 36)
	new_length = length + int(new_length_token.replace(">", "+").replace("<", "-"), 36)

	operations = []

	for attributes_tokens, newline_token, characters_token in operation_tokens:
		attributes = tuple(int(attribute[1:], 36) for attribute in attributes_tokens)
		newlines = int(newline_token[1:], 36) if newline_token else 0

		sign = {"+": 1, "=": 0, "-": -1}[characters_token[0]]

		characters = int(characters_token[1:], 36)

		operations.append((attributes, newlines, (characters, sign)))

	return length, new_length, operations, bank


def tokenize_event_changeset(changeset):
	"""
		Split changeset text into simple tokens for futher parsing.
	"""
	event_pattern = "Z(:\w+)(<\w+|>\w+)([^$]+)\$(.*)"
	length_token, new_length_token, op_codes, bank = re.match(event_pattern, changeset, re.DOTALL).groups()

	operations_pattern = "((\*\w+)*)(\|\w+)?(\+\w+|-\w+|=\w+)"

	def opdata(data):
		attributes, temp, newline, characters = data
		attributes = tuple("*%s" % attribute for attribute in attributes.split("*") if attribute)

		return attributes, newline, characters

	operations = map(opdata, re.findall(operations_pattern, op_codes))

	return length_token, new_length_token, operations, bank
