from flask import Flask, request, abort
from flask_cors import CORS
from flask_sqlalchemy import Pagination
from models import setup_db, Question, Category, db

QUESTIONS_PER_PAGE = 10


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)
    CORS(app)
    """
    @TODO: Set up CORS. Allow '*' for origins. Delete the sample route after completing the TODOs
    """

    """
    @TODO: Use the after_request decorator to set Access-Control-Allow
    """
    @app.after_request
    def access_control(res):
        res.headers['Access-Control-Allow-Origin'] = '*'
        return res

    @app.route('/categories', methods=['GET'])
    def categories():
        query = Category.query.all()
        response = dict()
        for category in query:
            response[category.id] = category.type
        return {
            "categories": response
        }

    @app.route('/questions', methods=['GET'])
    def questions():
        query = Category.query.all()
        response = dict()
        for category in query:
            response[category.id] = category.type
        page_num = int(request.args.get('page', 1))
        paginated_questions = Question.query.paginate(page_num, 10, True)
        page_response = {
            "questions": [q.format() for q in paginated_questions.items],
            "total_questions": len(paginated_questions.items),
            "categories": response,
            "current_category": "" if len(paginated_questions.items) < 1 else
            Category.query.get(paginated_questions.items[0].category).type,
        }
        return page_response

    @app.route('/questions/<question_id>', methods=['DELETE'])
    def delete_question(question_id):
        question = Question.query.get(int(question_id))
        if question:
            question.delete()
            db.session.commit()
        else:
            return {'success': False, 'question_id': None}, 422
        return {
            'success': True,
            'question_id': int(question_id)
        }

    @app.route('/questions', methods=['POST'])
    def search_or_question():
        json_data = request.get_json(force=True)
        if len(json_data.keys()) <= 1:
            search_term = f"%{json_data.get('searchTerm')}%"
            if not search_term:
                abort(400)
            results = Question.query.filter(Question.question.ilike(search_term))

            response = {
                "questions": [q.format() for q in results],
                "total_questions": results.count(),
                "current_category": "" if len(results.all()) < 1 else Category.query.get(results[0].category).type
            }
            return response
        else:
            answer = json_data.get('answer')
            question_ = json_data.get('question')
            difficulty = json_data.get('difficulty')
            category_id = json_data.get('category')
            if not (answer and question_ and difficulty and category_id):
                abort(400)
            category = Category.query.get(int(category_id))
            question = Question(answer=answer, question=question_, difficulty=difficulty, category=category)
            category.questions_in_category.append(question)
            db.session.commit()

            return {'question': question.question, 'answer': question.answer,
                    'difficulty': question.difficulty, 'category': category.id}

    @app.route('/categories/<category_id>/questions')
    def category_questions(category_id):
        category = Category.query.get(int(category_id))
        if category:
            questions_under_category = Question.query.filter_by(category=int(category_id))
            response = {
                "questions": [q.format() for q in questions_under_category],
                "total_questions": questions_under_category.count(),
                "current_category": category.type
            }
            return response
        return {'message': 'Invalid category'}, 404

    @app.route('/quizzes', methods=['POST'])
    def quiz():
        json_data = request.get_json(force=True)
        previous_questions = json_data.get('previous_questions', [])
        category_type = json_data.get('quiz_category').get('type')
        if not category_type:
            abort(400)
        if not Category.query.filter_by(type=category_type):
            return {'success': False, 'message': 'invalid category type'}, 400
        new_question = Question.query.join(Category).filter(Question.id.not_in(previous_questions), Category.type.like(category_type))\
            .first()

        if new_question:
            return {
                "question": new_question.format()
            }
        else:
            return {
                "question": {}
            }

    @app.errorhandler(404)
    def resource_not_found(e):
        return {'message': 'resource not found'}, 404

    @app.errorhandler(405)
    def invalid_request_method(e):
        return {'message': 'invalid request method'}, 405

    @app.errorhandler(400)
    def bad_request(e):
        return {'message': 'bad request'}, 400

    @app.errorhandler(422)
    def semantically_incorrect_response(e):
        return {'message': 'unable to process request'}

    return app

