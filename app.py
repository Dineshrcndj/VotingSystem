from flask import Flask,render_template,request,url_for,redirect,flash,session
import mysql.connector
from flask_session import Session
from voter_id import gvoterid,gmemberid
mydb=mysql.connector.connect(user='root',password='admin',host='localhost',database='voting',auth_plugin='mysql_native_password')

app=Flask(__name__)
app.secret_key='1234'
app.config['SESSION_USER']='filesystem'
# Session(app)
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/voterregister',methods=['GET','POST'])
def voterregister():
    if request.method=='POST':
        name=request.form['name']
        age=request.form['age']
        # phone=request.form['phone']
        city=request.form['city']
        aadhar=request.form['aadhar']
        cursor=mydb.cursor()
        cursor.execute('select count(aadhar) from voters where aadhar=%s',[aadhar])
        count_aadhar=cursor.fetchone()
        if int(age)>=18 and count_aadhar[0]==0:
            voterid=gvoterid()
            print(voterid)
            cursor.execute('insert into voters(voter_id,name,age,city,aadhar) values(%s,%s,%s,%s,%s)',[voterid,name,str(age),city,aadhar])
            mydb.commit()
            cursor.close()
            flash(f'Save this {voterid} id for future references')
            # return redirect(url_for('voterlogin'))
            return redirect(url_for('voterlogin'))
        elif count_aadhar[0]==1:
            return 'Voter Already exists'
        else:
            return 'age less than 18'
    return render_template('voterregister.html')

@app.route('/voterlogin',methods=['GET','POST'])
def voterlogin():
    if request.method=='POST':
        voterid=request.form['voterid']
        aadhar=request.form['aadhar']
        cursor=mydb.cursor()
        cursor.execute('select count(voter_id) from voters where voter_id=%s',[voterid])
        count_voter=cursor.fetchone()
        if count_voter[0]==1:
            cursor.execute('select aadhar from voters where voter_id=%s',[voterid])
            daadhar=cursor.fetchone()
            print('daadhar : ',daadhar, 'aadhar : ',aadhar)
            if aadhar==daadhar[0]:
                session['user']=voterid
                return redirect(url_for('dashboard_voters'))
            else:
                return 'invalid password' and redirect(url_for('voterlogin'))
        else:
            return 'no voter found'
    return render_template('voterlogin.html')

@app.route('/memberregister',methods=['GET','POST'])
def memberregister():
    if request.method=='POST':
        name=request.form['name']
        age=request.form['age']
        # phone=request.form['phone']
        city=request.form['city']
        partyname=request.form['party_name']
        cursor=mydb.cursor()
        cursor.execute('select count(party_name) from members where party_name=%s',[partyname])
        count_partyname=cursor.fetchone()
        if count_partyname[0]==0:
            memberid=gmemberid()
            print(memberid)
            cursor.execute('insert into members(member_id,name,age,city,party_name) values(%s,%s,%s,%s,%s)',[memberid,name,str(age),city,partyname])
            mydb.commit()
            cursor.execute('insert into results(party_name) values(%s)',[partyname])
            mydb.commit()
            cursor.close()
            flash(f'Save this {memberid} id for future references')
            # return redirect(url_for('voterlogin'))
            return redirect(url_for('memberlogin'))
        elif count_partyname[0]==1:
            return 'Party Name Already exists'
        else:
            return 'Something went wrong'
    return render_template('memberregister.html')

@app.route('/dashboard_voters')
def dashboard_voters():
    cursor=mydb.cursor()
    cursor.execute('select name,party_name from members')
    data=cursor.fetchall()
    cursor.execute('select name from voters where voter_id=%s',[session['user']])
    name=cursor.fetchone()
    return render_template('dashboard_voters.html',data=data,voter_id=session['user'],name=name[0])

@app.route('/voted_voters/<vote>')
def voted_voters(vote):
    cursor=mydb.cursor()
    cursor.execute('select count(voter_id) from voted_voter where voter_id=%s',[session['user']])
    count=cursor.fetchone()
    if count[0]==0:
        cursor.execute('insert into voted_voter(party_name,voter_id) values(%s,%s)',[vote,session['user']])
        mydb.commit()
        cursor.execute('select count(party_name) from voted_voter where party_name=%s',[vote])
        vote_count=cursor.fetchone()
        cursor.execute('UPDATE results SET votes_count = %s WHERE party_name = %s',[vote_count[0],vote])
        mydb.commit()
    else:
        return 'already voted'
    return 'Voted Successfully'

@app.route('/memberlogin',methods=['GET','POST'])
def memberlogin():
    if request.method=='POST':
        memberid=request.form['memberId']
        cursor=mydb.cursor()
        cursor.execute('select count(member_id) from members where member_id=%s',[memberid])
        count_mid=cursor.fetchone()
        if count_mid[0]==1:
            session['member']=memberid
            return redirect(url_for('dashboard_member'))
        else:
            return 'Invalid memberID'
    return render_template('memberlogin.html')

@app.route('/dashboard_member')
def dashboard_member():
    cursor=mydb.cursor()
    cursor.execute('select party_name from members where member_id=%s',[session['member']])
    party_name=cursor.fetchone()
    cursor.execute('SELECT vv.party_name, vv.voter_id, v.name from voted_voter vv left join voters v on vv.voter_id=v.voter_id where VV.party_name=%s',[party_name[0]])
    data=cursor.fetchall()
    print('data is ',data)
    cursor.execute('select count(party_name) from voted_voter where party_name=%s',[party_name[0]])
    countp=cursor.fetchone()
    return render_template('dashboard_member.html',data=data,count=countp)







@app.route('/admin')
def admin():
    cursor=mydb.cursor()
    cursor.execute('select party_name from members')
    party_names=cursor.fetchall()
    for i in party_names:
            cursor.execute('select count(party_name) from voted_voter where party_name=%s',[i[0]])
            vote_count=cursor.fetchone()
            cursor.execute('UPDATE results SET votes_count = %s WHERE party_name = %s',[vote_count[0],i[0]])
            mydb.commit()
    cursor.execute('select * from members')
    members=cursor.fetchall()
    cursor.execute('select * from results order by votes_count desc')
    results=cursor.fetchall()
    cursor.execute('select * from voted_voter')
    voted_voters=cursor.fetchall()
    cursor.execute('select * from voters')
    voters=cursor.fetchall()
    return render_template('admin.html',members=members,results=results,voted_voters=voted_voters,voters=voters)
app.run(use_reloader=True,debug=True)