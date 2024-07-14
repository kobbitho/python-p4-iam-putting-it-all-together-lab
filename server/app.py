#!/usr/bin/env python3
from flask import jsonify, request, session
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError, OperationalError

from config import app, db, api
from models import User, Recipe

class Signup(Resource):
    def post(self):
        data = request.get_json()

        username = data.get('username')
        password = data.get('password')
        image_url = data.get('image_url')
        bio = data.get('bio')

        if not username or not password:
            return jsonify({'message': 'Username and password are required.'}), 422

        user = User(
            username=username,
            image_url=image_url,
            bio=bio
        )
        user.password_hash = password

        try:
            db.session.add(user)
            db.session.commit()

            session['user_id'] = user.id

            return user.to_dict(), 201

        except IntegrityError:

            return {'error': '422'}, 422

class CheckSession(Resource):
    def get(self):
        user_id = session.get('user_id')

        if user_id:
            try:
                user = User.query.filter_by(id=user_id).first()
                if user:
                    return user.to_dict(), 200
            except OperationalError:
                return {'error': 'Database error'}, 500
        else:
            return {'error': 'Unauthorized'}, 401

class Login(Resource):
    def post(self):
        recived_request = request.get_json()

        username = recived_request.get('username')
        password = recived_request.get('password')
        
        user = User.query.filter_by(username=username).first()

        if user:
            if user.authenticate(password):
                session['user_id'] = user.id
                return user.to_dict(), 200
            
        return {'error': 'Invalid username or password'}, 401

class Logout(Resource):
    def delete(self):
        user_id = session.get('user_id')

        if user_id:
            session.pop('user_id', None)
            return '', 204
        else:
            return {'error': 'Unauthorized'}, 401


class RecipeIndex(Resource):
    def get(self):
        if session['user_id']:
            user = User.query.filter_by(id = session['user_id']).first()
            return [recipe.to_dict() for recipe in user.recipes], 200
        return {'error': 'Unauthorized'}, 401
    
    def post(self):
        user_id = session.get('user_id')

        if user_id:
            user = User.query.filter_by(id=user_id).first()
            data = request.get_json()

            title = data.get('title')
            instructions = data.get('instructions')
            minutes_to_complete = data.get('minutes_to_complete')

            if title and instructions and minutes_to_complete:
                recipe = Recipe(title=title, instructions=instructions, minutes_to_complete=minutes_to_complete)
                user.recipes.append(recipe)

                try:
                    db.session.add(recipe)
                    db.session.commit()
                    return recipe.to_dict(), 201
                except IntegrityError:
                    return {'error': 'Database error'}, 500
            else:
                return {'error': 'Invalid recipe data'}, 422
        else:
            return jsonify({'error': 'Unauthorized'}), 401


api.add_resource(Signup, '/signup', endpoint='signup')
api.add_resource(CheckSession, '/check_session', endpoint='check_session')
api.add_resource(Login, '/login', endpoint='login')
api.add_resource(Logout, '/logout', endpoint='logout')
api.add_resource(RecipeIndex, '/recipes', endpoint='recipes')


if __name__ == '__main__':
    app.run(port=5555, debug=True)