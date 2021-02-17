"""Routes for user authentication."""
from flask import Blueprint


# Blueprint Configuration
auth_bp = Blueprint(
    'auth_bp', __name__,
    template_folder='templates',
    static_folder='static'
)


@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    """
    User sign-up page.

    GET requests serve sign-up page.
    POST requests validate form & user creation.
    """
    form = SignupForm()
    # validate if the user filled out the form correctly
    # validate_on_submit is a built-in method
    if form.validate_on_submit():
    	# make sure it's not an existing user
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user is None:
        	# create a new user
            user = User(
                name=form.name.data,
                email=form.email.data,
                website=form.website.data
            )
            # use our set_password method
            user.set_password(form.password.data)
            # commit our new user record and log the user in
            db.session.add(user)
            db.session.commit()  # Create new user
            login_user(user)  # Log in as newly created user - from flask_login
            # if everything goes well, they will be redirected to the main application
            return redirect(url_for('main_bp.dashboard'))
        flash('A user already exists with that email address.')
    return render_template(
        'signup.jinja2',
        title='Create an Account.',
        form=form,
        template='signup-page',
        body="Sign up for a user account."
    )