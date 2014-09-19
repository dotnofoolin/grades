from flask import Flask, render_template
from datetime import date, timedelta, datetime
import json

from model import *

app = Flask(__name__)


def avg_to_letter(grade_average):
    grade_letter = ""
    if grade_average >= 90.0:
        grade_letter = "A"
    elif 80.0 <= grade_average <= 89.9:
        grade_letter = "B"
    elif 70.0 <= grade_average <= 79.9:
        grade_letter = "C"
    elif 60.0 <= grade_average <= 69.9:
        grade_letter = "D"
    elif grade_average <= 59.9:
        grade_letter = "F"

    return grade_letter


@app.route("/")
def index():
    # This is the data struct to send to the template. It's big!
    child_class_grades = []

    # Iterate each child...
    for child_object in Child.select():
        grades = []
        chart_labels = {}
        chart_data = {}
        chart_colors = {}
        overall_grade_average_sum = 0.0

        # Iterate each childs class...
        for class_object in Class.select().join(Child).where(Child.id == child_object.id):

            # Get the most recent grade for this class
            grade_object = Grade.select().join(Class).where(Class.id == class_object.id).order_by(Grade.post_date.desc()).limit(1).get()
            grades.append({
                'grade_id': grade_object.id,
                'class_id': grade_object.class_table.id,
                'class_name': grade_object.class_table.class_name,
                'color': grade_object.class_table.color,
                'grade_letter': grade_object.grade_letter,
                'grade_average': grade_object.grade_average,
                'post_date': grade_object.post_date,
                'report_text': grade_object.report_text,
            })

            overall_grade_average_sum += grade_object.grade_average

        # Cumulative grades for this child
        overall_grade_average = overall_grade_average_sum / len(grades)
        overall_grade_letter = avg_to_letter(overall_grade_average)

        # Get all the grades for trend charts. Select all dates greater than 30 days ago
        dates = Grade.select(Grade.post_date).join(Class).join(Child).where(Grade.post_date >= date.today()-timedelta(days=30), Child.id == child_object.id).group_by(Grade.post_date).order_by(Grade.post_date.asc())
        for d in dates:
            chart_labels[d.post_date.strftime('%Y-%m-%d')] = True

            # Manually get the grades for each date, set it to some value if not found
            for c in Class.select().join(Child).where(Child.id == child_object.id):
                try:
                    grade_per_class = Grade.select().where(Grade.post_date == d.post_date, Grade.class_table == c.id).get()
                    chart_data.setdefault(c.class_name, []).append(round(grade_per_class.grade_average, 0))
                except:
                    # If no grade for this date, just use the average grade for the whole class.
                    grade_per_class = Grade.select(fn.avg(Grade.grade_average).alias('gpa')).where(Grade.class_table == c.id).get()
                    chart_data.setdefault(c.class_name, []).append(round(grade_per_class.gpa, 0))

                chart_colors[c.class_name] = c.color


        # Build up that big data structure for the template
        child_class_grades.append({
            'child_name': child_object.child_name,
            'child_id': child_object.id,
            'overall_grade_letter': overall_grade_letter,
            'overall_grade_average': overall_grade_average,
            'grades': grades,
            'chart_labels': json.dumps(list(sorted(chart_labels.keys()))),
            'chart_data': chart_data,
            'chart_colors': chart_colors,
        })


    return render_template("index.html", child_class_grades=child_class_grades)


if __name__ == '__main__':
    app.run(debug=DEBUG)