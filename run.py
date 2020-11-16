from flask import Flask, render_template, redirect
from wtforms import *
from flask_wtf import FlaskForm
from wtforms.validators import InputRequired
import notion_charts

app = Flask(__name__)
app.config['SECRET_KEY'] = '6EFiWos8bvji3dps8H9J'


class LoginForm(FlaskForm):
    token = StringField('token', validators=[InputRequired()], render_kw={"placeholder": "156 char long code"})
    pageurl = StringField('pageurl', validators=[InputRequired()], render_kw={"placeholder": "Link to your page"})
    tableurl = StringField('tableurl', validators=[InputRequired()], render_kw={"placeholder": "Link to your table"})

    chart_types = [('bar', 'Bar (Horizontal)'), ('column', 'Column (Vertical)'), ('line', 'Line'), ('pie', 'Pie'), ('donut', 'Donut')]
    chart_type = SelectField('chart_type', choices=chart_types, validators=[InputRequired()])

    stacked = BooleanField('stacked', render_kw={"placeholder": "Stacked?"})

    theme_options = [('lightTheme', 'Light Mode'), ('darkTheme', 'Dark Mode')]
    theme = SelectField('theme', choices=theme_options, validators=[InputRequired()])

    legend_options = [('right', 'Right'), ('bottom', 'Bottom')]
    legend_position = SelectField('legend_position', choices=legend_options, validators=[InputRequired()])

    skip_non_numerical_values = BooleanField('skip_non_numerical_values', validators=[InputRequired()])


@app.route("/home", methods=["POST", "GET"])
def home():
    form = LoginForm()
    if form.validate_on_submit():
        token = form.token.data
        pageurl = form.pageurl.data
        tableurl = form.tableurl.data
        chart_type = form.chart_type.data
        stacked = form.stacked.data
        if stacked:
            if chart_type == 'bar' or chart_type == 'column':
                stacked = 'true'
            else:
                stacked = 'false'
        else:
            stacked = 'false'
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
        return render_template('index.html', form=form, text='Your chart got inserted!', source='../static/img/party_face.png')
    else:
        return render_template('index.html', form=form, text='')


@app.route("/table/<data>")
def table(data):
    data = data.split('§')
    return redirect("https://google.com")


if __name__ == "__main__":
    app.run(debug=True)

