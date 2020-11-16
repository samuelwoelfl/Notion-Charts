from flask import Flask, render_template, request, redirect, url_for
from wtforms import *
from flask_wtf import FlaskForm
from wtforms.validators import InputRequired, Email, Length
from datetime import datetime
import notion_charts

app = Flask(__name__)
app.config['SECRET_KEY'] = '6EFiWos8bvji3dps8H9J'

class LoginForm(FlaskForm):
    token = StringField('token', validators=[InputRequired()], render_kw={"placeholder": "156 char long code"})
    pageurl = StringField('pageurl', validators=[InputRequired()], render_kw={"placeholder": "Link to your page"})
    tableurl = StringField('tableurl', validators=[InputRequired()], render_kw={"placeholder": "Link to your table"})
    chart_types = [('bar', 'Bar (Horizontal)'), ('column', 'Column (Vertical)'), ('line', 'Line'), ('pie', 'Pie'), ('donut', 'Donut')]
    chart_type = SelectField('chart_type', choices = chart_types, validators=[InputRequired()])
    # chart_type = StringField('chart_type', validators=[InputRequired()], render_kw={"placeholder": "Chart Type"})
    stacked = StringField('stacked', validators=[InputRequired()], render_kw={"placeholder": "Stacked?"})
    theme = StringField('theme', validators=[InputRequired()], render_kw={"placeholder": "Notion Theme"})
    legend_position = StringField('legend_position', validators=[InputRequired()], render_kw={"placeholder": "Legend Position"})
    skip_non_numerical_values = StringField('skip_non_numerical_values', validators=[InputRequired()], render_kw={"placeholder": "Skip non numerical Values?"})


@app.route("/home", methods=["POST", "GET"])
def home():
    form = LoginForm()
    if form.validate_on_submit():
        token = form.token.data
        pageurl = form.pageurl.data
        tableurl = form.tableurl.data
        chart_type = form.chart_type.data
        print(chart_type)
        stacked = form.stacked.data
        theme = form.theme.data
        legend_position = form.legend_position.data
        skip_non_numerical_values = form.skip_non_numerical_values.data

        Notion = notion_charts.NotionAPI(token)
        data_frame = Notion.get_data(tableurl, skip_non_numerical_values)

        Doc = notion_charts.GoogleSheets()
        start = Doc.write_frame_get_start(data_frame)
        id = Doc.id[0]
        range = notion_charts.get_range(start, id)

        link = notion_charts.generate_chart_link(range, chart_type, stacked, theme, legend_position)

        Notion.insert_chart(pageurl, link)
        return render_template('index.html', form=form, text='finished')
    else:
        return render_template('index.html', form=form, text='')

@app.route("/table/<data>")
def table(data):
    data = data.split('§')
    return redirect("https://google.com")


if __name__ == "__main__":
    app.run(debug=True)

