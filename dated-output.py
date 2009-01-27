"""
dated-output plugin for rawdog, by Adam Sampson <ats@offog.org>

Needs rawdog 2.5rc1 or later, and Python 2.5.

Rather than writing a single output file, this plugin splits the output
into several files by date. The "pagedateformat" strftime format is used
to generate the filenames; it'll switch to a new output file when the
date that produces changes. The newest output file will get the default name,
and older ones will have a "-date" suffix inserted before the last ".".

This also generates a __paged_output_pages__ bit in the main template
that lists the files produced.

It is assumed that you're using rawdog's default article sorting mechanism.
If you're using another plugin that orders the articles differently, this
will not work very well.
"""

import os, time, datetime, calendar
import rawdoglib.plugins
from rawdoglib.rawdog import DayWriter, write_ascii, format_time, fill_template, safe_ftime
from StringIO import StringIO

class DatedOutput:
	def __init__(self):
		self.page_date_format = "%Y-%m-%d"

		self.output_files = {}
		self.current_date = None
		self.current_fn = None
		self.f = None
		self.dw = None

	def config_option(self, config, name, value):
		if name == "pagedateformat":
			self.page_date_format = value
			return False
		else:
			return True

	def generate_list(self, rawdog, config):
		"""Generate the list of pages."""

		f = StringIO()

		# Sort and reverse the list of dates, so we have the newest
		# first.
		dates = self.output_files.keys()
		dates.sort()
		dates.reverse()

		f.write('<ul class="paged_output_pages">\n')
		for date in dates:
			fn = self.output_files[date]

			f.write('<li>')
			if fn != self.current_fn:
				f.write('<a href="' + os.path.basename(fn) + '">')
			f.write(date)
			if fn != self.current_fn:
				f.write('</a>')
			f.write('</li>\n')
		f.write('</ul>\n')

		return f.getvalue()

	def generate_calendar(self, rawdog, config):
		"""Generate the calendar."""

		month_head_format = '%B %Y'
		day_head_format = '%a'
		day_format = '%d'

		t = time.strptime(self.current_date, self.page_date_format)
		this_month = datetime.date(t.tm_year, t.tm_mon, 1)
		cal = calendar.Calendar()

		# Find links to the previous and next months, if they exist.
		prev_date = None
		next_date = None
		dates = self.output_files.keys()
		dates.sort()
		for date in dates:
			t = time.strptime(date, self.page_date_format)
			that_month = datetime.date(t.tm_year, t.tm_mon, 1)

			if that_month < this_month:
				prev_date = date
			if that_month > this_month:
				next_date = date
				break

		f = StringIO()

		f.write('<table class="calendar">\n')

		# Print the previous/month name/next bar.
		f.write('<tr class="cal-head">\n')
		f.write('<td class="cal-prev">')
		if prev_date is not None:
			f.write('<a href="%s">&lt;</a>' % os.path.basename(self.output_files[prev_date]))
		f.write('</td>\n')
		f.write('<td class="cal-month" colspan="5">%s</td>\n' % this_month.strftime(month_head_format))
		f.write('<td class="cal-next">')
		if next_date is not None:
			f.write('<a href="%s">&gt;</a>' % os.path.basename(self.output_files[next_date]))
		f.write('</td>\n')
		f.write('</tr>\n')

		# Print the day-names bar.
		f.write('<tr>\n')
		for day in cal.iterweekdays():
			# Find a date that corresponds to the day number we
			# want to print. I don't see a better way to do this
			# in datetime...
			date = datetime.date(1981, 9, 25)
			while date.weekday() != day:
				date += datetime.timedelta(days = 1)

			f.write('<th>%s</th>' % date.strftime(day_head_format))
		f.write('</tr>\n')

		# Print the weeks of the month.
		for week in cal.monthdatescalendar(this_month.year, this_month.month):
			f.write('<tr class="cal-week">\n')
			for day in week:
				date = day.strftime(self.page_date_format)

				f.write('<td class="cal-day">')
				if day.month != this_month.month:
					f.write('<em class="cal-othermonth">')
					after = '</em>'
				elif date == self.current_date:
					f.write('<strong class="cal-current">')
					after = '</strong>'
				elif date in self.output_files:
					f.write('<a class="cal-link" href="' + os.path.basename(self.output_files[date]) + '">')
					after = '</a>'
				else:
					after = ''
				f.write(day.strftime(day_format))
				f.write(after)
				f.write('</td>')
			f.write('</tr>\n')

		f.write('</table>\n')

		return f.getvalue()

	def write_output(self, rawdog, config):
		"""Write out the current output file."""

		bits = rawdog.get_main_template_bits(config)
		bits["items"] = self.f.getvalue()
		bits["num_items"] = str(len(rawdog.articles.values()))
		bits["paged_output_pages"] = self.generate_list(rawdog, config)
		bits["calendar"] = self.generate_calendar(rawdog, config)

		s = fill_template(rawdog.get_template(config), bits)
		fn = self.current_fn
		config.log("dated-output writing output file: ", fn)
		f = open(fn + ".new", "w")
		write_ascii(f, s, config)
		f.close()
		os.rename(fn + ".new", fn)

	def set_filename(self, rawdog, config, fn):
		"""Set the output filename. If it changes, switch to a new
		output file. If set to None, close the current output file."""

		if fn == self.current_fn:
			return

		if self.current_fn is not None:
			self.dw.close()
			self.write_output(rawdog, config)

		if fn is not None:
			self.f = StringIO()
			self.dw = DayWriter(self.f, config)

		self.current_fn = fn

	def output_write_files(self, rawdog, config, articles, article_dates):
		config.log("dated-output starting")

		# Extract the prefix and suffix from the configured outputfile.
		outputfile = config["outputfile"]
		i = outputfile.rfind('.')
		if i != -1:
			prefix = outputfile[:i]
			suffix = outputfile[i:]
		else:
			prefix = outputfile
			suffix = ""

		# Figure out the output filename date for each article.
		article_fn_dates = {}
		self.output_files = {}
		for article in articles:
			tm = time.localtime(article_dates[article])
			date = safe_ftime(self.page_date_format, tm)
			article_fn_dates[article] = date

			if date in self.output_files:
				pass
			elif self.output_files == {}:
				# First output file: use the configured name.
				self.output_files[date] = outputfile
			else:
				# Otherwise use a dated name.
				self.output_files[date] = "%s-%s%s" % (prefix, date, suffix)

		# Write out each article.
		for article in articles:
			date = article_fn_dates[article]
			self.set_filename(rawdog, config, self.output_files[date])
			self.current_date = date

			self.dw.time(article_dates[article])
			rawdog.write_article(self.f, article, config)

		self.set_filename(rawdog, config, None)

		config.log("dated-output done")
		return False

p = DatedOutput()
rawdoglib.plugins.attach_hook("config_option", p.config_option)
rawdoglib.plugins.attach_hook("output_write_files", p.output_write_files)
