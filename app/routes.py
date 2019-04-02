import os
import secrets
from PIL import Image
from flask import render_template, url_for, flash, redirect, request, abort
from app import app, db, bcrypt
from app.forms import RegistrationForm, LoginForm, UpdateAccountForm, CampaignForm, DonationForm
from app.models import User, Campaign, Donation
from flask_login import login_user, current_user, logout_user, login_required



@app.route("/home")
@login_required
def home():
    campaigns = Campaign.query.all()
    return render_template('home.html', campaigns=campaigns)


@app.route("/")
@app.route("/about")
def about():
    return render_template('about.html', title='About')


@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))


def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/profile_pics', picture_fn)

    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn


@app.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    return render_template('account.html', title='Account',
                           image_file=image_file, form=form)


@app.route("/campaign/new", methods=['GET', 'POST'])
@login_required
def new_campaign():
    form = CampaignForm()
    if form.validate_on_submit():
        campaign = Campaign(title=form.title.data, content=form.content.data,
                            author=current_user, amount=form.amount.data)
        db.session.add(campaign)
        db.session.commit()
        flash('Your campaign has been created!', 'success')
        return redirect(url_for('home'))
    return render_template('create_campaign.html', title='New Campaign',
                           form=form, legend='New Campaign')


@app.route("/campaign/<int:campaign_id>")
def campaign(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    return render_template('campaign.html', title=campaign.title, campaign=campaign)


@app.route("/campaign/<int:campaign_id>/update", methods=['GET', 'POST'])
@login_required
def update_campaign(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    if campaign.author != current_user:
        abort(403)
    form = CampaignForm()
    if form.validate_on_submit():
        campaign.title = form.title.data
        campaign.content = form.content.data
        db.session.commit()
        flash('Your campaign has been updated!', 'success')
        return redirect(url_for('campaign', campaign_id=campaign.id))
    elif request.method == 'GET':
        form.title.data = campaign.title
        form.content.data = campaign.content
    return render_template('create_campaign.html', title='Update Campaign',
                           form=form, legend='Update Campaign')


@app.route("/campaign/<int:campaign_id>/delete", methods=['POST'])
@login_required
def delete_campaign(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    if campaign.author != current_user:
        abort(403)

    for donation in campaign.donations:
        db.session.delete(donation)
    db.session.delete(campaign)
    db.session.commit()
    flash('Your Campaign has been deleted!', 'success')
    return redirect(url_for('home'))


@app.route("/campaign/<int:campaign_id>/donation", methods=['GET', 'POST'])
@login_required
def donation(campaign_id):
    form = DonationForm()
    campaign = Campaign.query.get_or_404(campaign_id)
    if form.validate_on_submit():
        donation = Donation(title=form.title.data, campaign=campaign, user_id=current_user.username,
                            amount=form.amount.data)
        db.session.add(donation)
        db.session.commit()
        flash('Your Donation has been added!', 'success')
        return redirect(url_for('home'))
    return render_template('donation.html', title='New Donation',
                           form=form, legend='New Donation')


@app.route("/done_campaigns")
@login_required
def done_campaigns():
    campaigns = Campaign.query.all()
    return render_template('done_campaigns.html', title='Done Campaigns', campaigns=campaigns)
