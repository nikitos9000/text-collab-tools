def h(text): # helper for key
	import re
	return re.escape(text).replace("\#", "\w+").replace("\ ", "\s+")

def v(text): # helper for value
	return text.replace("\#", "\g<1>")


# Section is a list of tuples (key, name, children),
# where key is a regular expression, name - is a replacement for found key,
# children is a recursive list of same tuples, '#' symbol is for matching.
sections = [
	[
		(h("Case #"), None)
	], [
		(h("Case 1: Select a product and collectively write a review."), None, [
			(h("1.1 Please select a product catogory from the following list"), v("Product category")),
			(h("1.2 Product brand"), v("Product brand")),
			(h("1.3 Product model"), v("Product model")),
			(h("1.4 Title for your review"), v("Review title")),
			(h("1.5 How do you rate this item?"), v("Item rating")),
			(h("1.6 Your review"), v("Review text")),
		]),

		(h("Case 2: How many different ways can we use a brick?"), None, [
			(h("Idea #"), v("Idea"))
		]),

		(h("Case 3: Imagine that you are a college principal and you needed to judge a moral dilemma."), None, [
			(h("The student's (#) grade on the exam"), v("Decision on student's grade"), [
				(h("Reason:"), v("Reason for student's grade"))
			]),

			(h("The student's (#) status on the athletic team"), v("Decision on student's athletic team status"), [
				(h("Reason:"), v("Reason for student's athletic team status"))
			]),

			(h("The student's (#) academic status"), v("Decision on student's academic status"), [
				(h("Reason:"), v("Reason for student's academic status"))
			]),

			(h("The teaching assistant's (#) work status"), v("Decision on teaching assistant's work status"), [
				(h("Reason:"), v("Reason for teaching assistant's work status"))
			]),

			(h("The teaching assistant's (#) academic status"), v("Decision on teaching assistant's academic status"), [
				(h("Reason:"), v("Reason for teaching assistant's academic status"))
			]),
		]),

		(h("Case 4: Please summarize the text below in two or three sentences."), v("Summary")),
		(h("Case 5: Mathematics"), v("Answer")),
]]
