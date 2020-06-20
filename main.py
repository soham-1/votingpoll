from flask import Flask, render_template, request, session, redirect
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
import json
 
# use write_params() method in admin related functions to improve dynamicity
def get_params():
    with open('config.json', 'r') as c:
        params = json.load(c)['params']
    return params
params = get_params()
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = params['database_uri']
app.secret_key = params['secret_key']
db = SQLAlchemy(app)

# make database accordingly in database server. Emailid in all other tables are foreign keys from accounts table
class Accounts(db.Model):
    name = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(20), nullable=False)
    emailid = db.Column(db.String(120), primary_key=True)
    division = db.Column(db.String(10), nullable=False)
    gender = db.Column(db.String(1), nullable=False)

# application form for standing in elections are registered here
class Represent(db.Model):
    name = db.Column(db.Text, nullable=False)
    field = db.Column(db.String(20), primary_key=True)
    division= db.Column(db.String(10), nullable=False)
    emailid = db.Column(db.String(100), primary_key=True)
    bio = db.Column(db.String(200), nullable=False)
    # image = db.Column(db.String(200), nullable=False)  try to add image column in database

# maintains the vote count for representatives
class Votecount(db.Model):
    email = db.Column(db.String(100), primary_key=True)
    field = db.Column(db.String(20), nullable=False)
    division = db.Column(db.String(10), nullable=False)
    votecount = db.Column(db.INT, nullable=False)
    gender = db.Column(db.String(1), nullable=False)

# maintains the entries of peopele who have voted to restrain from voting 2nd time
class Voted(db.Model):
    email = db.Column(db.String(100), primary_key=True)
    field = db.Column(db.String(10), primary_key=True)
    gender = db.Column(db.String(1), primary_key=True)

# landing page
@app.route('/')
def homepage():
    return render_template('index.html')

# next time use login_required decorator in all functions!!
@app.route('/signup', methods=['GET', 'POST'])
def do_signup():
    params = get_params()
    if request.method == 'POST':
        data = request.form
        username = data['username']
        passwd = data['pass']
        emailid = data['email']
        re_pass = data['re_pass']
        division = data['division']
        gender = data['gender']

        if passwd != re_pass:
            return render_template('signup.html')
        
        else:
            is_acc = Accounts.query.filter(Accounts.emailid==emailid).first()
            if is_acc:
                return render_template('signup.html')
            else:
                newuser = Accounts(name=username, password=passwd, emailid=emailid, division=division, gender=gender)
                db.session.add(newuser)
                db.session.commit()
                session['user'] = emailid
                return redirect('/main')

    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def do_login():
    params = get_params()
    if 'user' in session:
        if session['user'] == 'admin':
            return redirect('/admin')
        elif session['user'] and session['user'] != 'admin' :
            return redirect('/main')

    if request.method == 'POST':
        data = request.form
        username = data['username']
        passwd = data['passwd']

        if username==params['adminuser'] and passwd==params['adminpass']:
            session['user'] = username
            return redirect('/admin')

        is_acc = Accounts.query.filter(Accounts.name==username, Accounts.password==passwd).first()
        if is_acc:
            session['user'] = is_acc.emailid
            return redirect('/main')
        else:
            return render_template('login.html')

    return render_template('login.html')

@app.route('/logout')
def logout():
    del session['user']
    return redirect('/')

#=====================================================student panel================================================================

# homepage for students
@app.route('/main')
def mainpage():
    params = get_params()
    if 'user' in session and session['user'] != 'admin':
        if session['user'] == 'admin':
            return redirect('/admin')
        else:
            active_elections = params['active_elections']
            active_council_names = params['active_council_names']
            return render_template('main.html', active_elections=active_elections, active_council_names=active_council_names)
    return redirect('/login')

# opens application form
@app.route('/apply')
def apply_candidature():
    if 'user' in session and session['user'] != 'admin':          
        return redirect('/apply_form')
    return redirect('/login')

# submits application form
@app.route('/apply_form', methods=['GET', 'POST'])
def apply_form():
    params = get_params()
    if 'user' in session and session['user'] != 'admin':
        if request.method == 'POST':
            data = request.form
            fullname = data['fullname']
            emailid = data['emailid']
            division = data['division']
            field = data['field']
            bio = data['bio']
            try:
                newapplicant = Represent(name=fullname, emailid=emailid, division=division, field=field, bio=bio)
                db.session.add(newapplicant)
                db.session.commit()
                return redirect('/main')
            except Exception as e:
                print(e)
                return redirect('/apply_form')
        return render_template('applyform.html')
    return redirect('/login')

# dynamically creates page according to selected field to vote and also handles the vote submission form
@app.route('/vote', methods=['GET', 'POST'])
def cast_vote():
    params = get_params()
    if 'user' in session and session['user'] != 'admin':
        if 'id' in request.args.keys():
            selfemail = session['user'] # had to use this line as it was not working directly in query line
            userdiv = Accounts.query.filter(Accounts.emailid==selfemail).first()
            page = int(request.args['id'])
            council_dict = { x:y for x,y in enumerate(params['active_council_names'])}
            selectedfield = council_dict[page]
            print(selectedfield)
            print(session['user'])
            names = Represent.query.filter(Represent.field==selectedfield, Represent.division==userdiv.division).all()
            votedForBoy = Voted.query.filter(Voted.email==session['user'], Voted.gender=='m', Voted.field==selectedfield).first()
            votedForGirl = Voted.query.filter(Voted.email==session['user'], Voted.gender=='f', Voted.field==selectedfield).first()
            print(votedForBoy)
            boysname = []
            girlsname = []

            for i in names:
                boysname.extend(Accounts.query.filter(Accounts.emailid==i.emailid, Accounts.gender=='m').all())
            for i in names:
                girlsname.extend(Accounts.query.filter(Accounts.emailid==i.emailid, Accounts.gender=='f').all())

            boys=[]
            girls=[]
            for i in boysname:
                boys.extend(Represent.query.filter(Represent.emailid==i.emailid).all())
            for i in girlsname:
                girls.extend(Represent.query.filter(Represent.emailid==i.emailid).all())
            # print(girls[0].emailid)
            return render_template('vote.html', boys=boys, nboys=len(boys), girls=girls, ngirls=len(girls), selectedfield=selectedfield, votedForBoy=votedForBoy, votedForGirl=votedForGirl)

        if request.args['targetvote']:
            print(request.args['targetvote'])
            field = request.args['selectedfield']
            div = Accounts.query.filter(Accounts.emailid==request.args['targetvote']).first().division
            gender = 'm' if request.args['boys'] == 'True' else 'f'
            cast_vote = Votecount.query.filter(Votecount.email==request.args['targetvote']).first()
            voted = Voted(email=session['user'], field=field, gender=gender)
            db.session.add(voted)
            db.session.commit()
            if cast_vote is None:
                query = Votecount(email=request.args['targetvote'], field=field,division=div,votecount=1, gender=gender)
                db.session.add(query)
                db.session.commit()
            else:
                cast_vote.votecount += 1
                db.session.commit()
            return redirect('/main')
    return redirect('/login')


#=====================================================admin panel================================================================
# add select_candidates() function so that candidates who apply for candidature shouldn't directly be listed. But first be approved by admin
# also add set_params() to overwrite config.json and make pages more dynamic

@app.route('/admin')
def admin():
    params = get_params()
    if 'user' in session and session['user'] == 'admin':
        active_elections = params['active_elections']
        active_council_names = params['active_council_names']
        return render_template('admin.html', active_elections=active_elections, active_council_names=active_council_names)  
    return redirect('/login')  

@app.route('/results')
def results():
    params = get_params()
    if 'user' in session and session['user'] == 'admin':
        selectedfield = request.args['id']
        selectedfield = params['active_council_names'][int(selectedfield)]
        boysresult=[]
        girlsresult=[]
        for div in params["divisions"]:
            res = db.session.query(func.max(Votecount.votecount), Votecount.email).filter(Votecount.field==selectedfield, Votecount.gender=='m', Votecount.division==div).all()
            res1 = db.session.query(func.max(Votecount.votecount), Votecount.email).filter(Votecount.field==selectedfield, Votecount.gender=='f', Votecount.division==div).all()
            if res:
                boysresult.append(res[0])
            if res1:
                girlsresult.append(res1[0])
        print(boysresult)
        print(girlsresult)
        paramgrid = {'boysresult': boysresult, 'girlsresult':girlsresult, 'division':params["divisions"]}
        return render_template('results.html', paramgrid=paramgrid)  
    return redirect('/login') 


app.run(debug=True)
