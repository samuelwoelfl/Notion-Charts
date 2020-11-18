from flask import Flask, render_template, redirect, make_response, request, jsonify
from wtforms import *
from flask_wtf import FlaskForm
from wtforms.validators import InputRequired
import notion_charts, time

app = Flask(__name__)
app.config['SECRET_KEY'] = '6EFiWos8bvji3dps8H9J'


class LoginForm(FlaskForm):
    token = StringField('token', validators=[InputRequired()], render_kw={"placeholder": "156 char long code"})
    pageurl = StringField('pageurl', validators=[InputRequired()], render_kw={"placeholder": "Link to your page"})
    tableurl = StringField('tableurl', validators=[InputRequired()], render_kw={"placeholder": "Link to your table"})

    chart_types = [('bar', 'Bar (Horizontal)'), ('column', 'Column (Vertical)'), ('line', 'Line'), ('pie', 'Pie'), ('donut', 'Donut'), ('geo', 'Map')]
    chart_type = SelectField('chart_type', choices=chart_types, validators=[InputRequired()])

    stacked = BooleanField('stacked', render_kw={"placeholder": "Stacked?"})

    region_options = [('AD', 'Andorra'),
                      ('AF', 'Afghanistan'),
                      ('AL', 'Albania'),
                      ('AR', 'Argentina'),
                      ('AT', 'Austria'),
                      ('AU', 'Australia'),
                      ('BE', 'Belgium'),
                      ('BG', 'Bulgaria'),
                      ('BR', 'Brazil'),
                      ('BS', 'Bahamas'),
                      ('BY', 'Belarus'),
                      ('CA', 'Canada'),
                      ('CL', 'Chile'),
                      ('CN', 'China'),
                      ('HR', 'Croatia'),
                      ('CZ', 'Czechia'),
                      ('DK', 'Denmark'),
                      ('EG', 'Egypt'),
                      ('FI', 'Finland'),
                      ('FR', 'France'),
                      ('DE', 'Germany'),
                      ('GB', 'Great Britain'),
                      ('IE', 'Ireland'),
                      ('IL', 'Israel'),
                      ('IN', 'India'),
                      ('IQ', 'Iraq'),
                      ('IR', 'Iran'),
                      ('IS', 'Iceland'),
                      ('IT', 'Italy'),
                      ('JP', 'Japan'),
                      ('KR', 'South Korea'),
                      ('LB', 'Lebanon'),
                      ('LI', 'Liechtenstein'),
                      ('LU', 'Luxembourg'),
                      ('LV', 'Latvia'),
                      ('MA', 'Morocco'),
                      ('MC', 'Monaco'),
                      ('ME', 'Montenegro'),
                      ('MG', 'Madagascar'),
                      ('MX', 'Mexico'),
                      ('MY', 'Malaysia'),
                      ('NA', 'Namibia'),
                      ('NG', 'Nigeria'),
                      ('NL', 'Netherlands'),
                      ('NO', 'Norway'),
                      ('NP', 'Nepal'),
                      ('NZ', 'New Zealand'),
                      ('PA', 'Panama'),
                      ('PE', 'Peru'),
                      ('PH', 'Philippines'),
                      ('PL', 'Poland'),
                      ('PT', 'Portugal'),
                      ('PY', 'Paraguay'),
                      ('QA', 'Qatar'),
                      ('RU', 'Russia'),
                      ('SA', 'Saudi Arabia'),
                      ('SD', 'Sudan'),
                      ('SE', 'Sweden'),
                      ('SG', 'Singapore'),
                      ('SI', 'Slovenia'),
                      ('SK', 'Slovakia'),
                      ('SL', 'Sierra Leone'),
                      ('SM', 'San Marino'),
                      ('SN', 'Senegal'),
                      ('SO', 'Somalia'),
                      ('SS', 'South Sudan'),
                      ('TH', 'Thailand'),
                      ('TR', 'Turkey'),
                      ('TV', 'Tuvalu'),
                      ('TW', 'Taiwan'),
                      ('UA', 'Ukraine'),
                      ('AE', 'United Arab Emirates'),
                      ('US', 'United States of America'),
                      ('UY', 'Uruguay'),
                      ('VE', 'Venezuela'),
                      ('LK', 'Sri Lanka'),
                      ('ES', 'Spain'),
                      ('CH', 'Switzerland'),
                      ]
    region = SelectField('region', choices=region_options)

    resolution_options = [('coutries', 'Countries'), ('provinces', 'Provinces'), ('metros', 'Metros - only available for US')]
    resolution = SelectField('resolution', choices=resolution_options)

    theme_options = [('lightTheme', 'Light Mode'), ('darkTheme', 'Dark Mode')]

    theme = SelectField('theme', choices=theme_options, validators=[InputRequired()])

    legend_options = [('right', 'Right'), ('bottom', 'Bottom')]
    legend_position = SelectField('legend_position', choices=legend_options, validators=[InputRequired()])

    customvalue = StringField('customvalue', render_kw={"placeholder": "eg. Amount;Visitors"})

    customcolor1 = StringField('customcolor1', render_kw={"placeholder": "#ff0000;#00ff00"})
    # customcolor2 = StringField('customcolor2', render_kw={"placeholder": "#00ff00"})
    # customcolor3 = StringField('customcolor3', render_kw={"placeholder": "#0000ff"})
    # customcolor4 = StringField('customcolor4', render_kw={"placeholder": "#ff0000"})
    # customcolor5 = StringField('customcolor5', render_kw={"placeholder": "#00ff00"})
    # customcolor6 = StringField('customcolor6', render_kw={"placeholder": "#0000ff"})

    skip_non_numerical_values = BooleanField('skip_non_numerical_values')


status_list = ['Make Magic']

@app.route('/_stuff', methods=['GET'])
def stuff():
    return jsonify(result=status_list[-1])

@app.route("/", methods=["POST", "GET"])
def home():
    form = LoginForm()
    if form.validate_on_submit():
        status_list.append('Fetching data from Notion')

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
        region = form.region.data
        resolution = form.resolution.data
        theme = form.theme.data
        legend_position = form.legend_position.data
        custom_value = form.customvalue.data
        if not custom_value:
            custom_value = ""
        else:
            custom_value = custom_value.split(';')
        try:
            colors = form.customcolor1.data.replace('#', '%23').replace(';', ',')
        except:
            colors = []
        skip_non_numerical_values = form.skip_non_numerical_values.data
        if not skip_non_numerical_values or skip_non_numerical_values == None or skip_non_numerical_values == '':
            skip_non_numerical_values = False

        try:
            Notion = notion_charts.NotionAPI(token)
        except:
            status_list.append('Error while fetching Notion data. Please check your token.')
            return render_template('index.html#bottom', form=form, text='', source='', success='', token=token)
        try:
            data_frame = Notion.get_data(tableurl, skip_non_numerical_values, custom_value)
        except:
            status_list.append('Error while fetching Notion data. Please check the URLs to your page and table.')
            return render_template('index.html#bottom', form=form, text='', source='', success='', token=token)

        status_list.append('Transferring data to google sheets')

        try:
            Doc = notion_charts.GoogleSheets()
            start, range = Doc.write_frame_get_start(data_frame)
            id = Doc.id[0]
        except:
            status_list.append('Error while transferring data to Google Sheets.')
            return render_template('index.html#bottom', form=form, text='', source='', success='', token=token)

        status_list.append('Generating link')

        try:
            link = notion_charts.generate_chart_link(range, chart_type, stacked, region, resolution, theme, legend_position, colors)
        except:
            status_list.append('Error while generating link.')
            return render_template('index.html#bottom', form=form, text='', source='', success='', token=token)

        status_list.append('Inserting Chart')

        try:
            Notion.insert_chart(pageurl, link)
        except:
            status_list.append('Error while inserting chart.')
            return render_template('index.html#bottom', form=form, text='', source='', success='', token=token)
        try:
            status_list.append('Make Magic')
            resp = make_response(render_template('index.html', form=form, text='Your chart got inserted!', source='../static/img/party_face.png', success='display'))
            resp.set_cookie('token_v2', token)
            return resp
        except:
            status_list.append('General Error')
            return render_template('index.html#bottom', form=form, text='', source='', success='', token=token)
    else:
        try:
            token = request.cookies.get('token_v2')
        except:
            token = ''
        return render_template('index.html', form=form, text='', source='', success='', token=token)


@app.route("/table/<data>")
def table(data):
    data = data.split('§')
    return redirect("https://google.com")


if __name__ == "__main__":
    app.run(debug=True)

