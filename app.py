import os
from flask import (
    Flask, flash, render_template,
    redirect, request, session, url_for)
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
if os.path.exists("env.py"):
    import env


app = Flask(__name__)

app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.secret_key = os.environ.get("SECRET_KEY")

mongo = PyMongo(app)


@app.route("/")
@app.route("/get_recipes")
def get_recipes():
    get_recipes = list(mongo.db.recipes.find())
    return render_template("get_recipes.html", get_recipes=get_recipes)


@app.route("/search", methods=["GET", "POST"])
def search():
    query = request.form.get("query")
    get_recipes = list(mongo.db.recipes.find({"$text": {"$search": query}}))
    return render_template("get_recipes.html", get_recipes=get_recipes)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # check if username is already taken
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            flash("Username not available")    
            return redirect(url_for("register"))

        register = {
            "username": request.form.get("username").lower(),
            "password": generate_password_hash(request.form.get("password"))
        }
        mongo.db.users.insert_one(register)

        # put new user into session cookie
        session["user"] = request.form.get("username").lower()
        flash("Congrats! You're in!")
        return redirect(url_for("profile", username=session["user"]))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # check if username already exists in database
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            # make sure that hashed password matches user's input
            if check_password_hash(
                existing_user["password"], request.form.get("password")):
                    session["user"] = request.form.get("username").lower()
                    flash("Welcome, {}".format( 
                        request.form.get("username")))
                    return redirect(url_for(
                        "profile", username=session["user"]))
            else:
                # in case of invalid password
                flash("Incorrect Username or/and Password")
                return redirect(url_for("login"))

        else:
            # username doesn't exist
            flash("Incorrect Username or/and Password")      
            return redirect(url_for("login"))
            
    return render_template("login.html")


@app.route("/profile/<username>", methods=["GET", "POST"])
def profile(username):
    # get the session user's name from the database
    username = mongo.db.users.find_one(
        {"username": session["user"]})["username"]

    if session["user"]:
        return render_template("profile.html", username=username)

    return redirect(url_for("login"))


@app.route("/logout")
def logout():
    # remove user from session cookies
    flash("You are now logged out")
    session.pop("user")
    return redirect(url_for("login"))


@app.route("/new_recipe", methods=["GET", "POST"])
def new_recipe():
    if request.method == "POST":
        recipe = {
            "recipe_name": request.form.get("recipe_name"),
            "ingredients": request.form.get("ingredients").splitlines(),
            "cooking_time": request.form.get("cooking_time"),
            "prep": request.form.get("prep").splitlines(),
            "categories": request.form.get("categories")
        }
        mongo.db.recipes.insert_one(recipe)
        flash("Recipe added!")
        return redirect(url_for("get_recipes"))

    categories = mongo.db.categories.find().sort("categories", 1)
    return render_template("new_recipe.html", categories=categories)

@app.route("/edit_recipe/<recipe_id>", methods=["GET", "POST"])
def edit_recipe(recipe_id):
    if request.method == "POST":
        submit = {
            "recipe_name": request.form.get("recipe_name"),
            "ingredients": request.form.get("ingredients"),
            "cooking_time": request.form.get("cooking_time"),
            "prep": request.form.get("prep"),
            "categories": request.form.get("categories")
            }
        mongo.db.tasks.update({"_id": ObjectId(task_id)}, submit)
        flash("Task Successfully Updated")

    recipe = mongo.db.tasks.find_one({"_id": ObjectId(recipe_id)})
    categories = mongo.db.categories.find().sort("categories", 1)
    return render_template("edit_recipe.html", recipe=recipe, categories=categories)


@app.route("/delete_recipe/<recipe_id>")
def delete_recipe(recipe_id):
    mongo.db.recipes.remove({"_id": ObjectId(recipe_id)})
    flash("Recipe Successfully Deleted")
    return redirect(url_for("get_recipes"))
  
if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=True)
