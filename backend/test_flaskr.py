import os
import unittest
import json
from flask_sqlalchemy import SQLAlchemy

from flaskr import create_app
from models import setup_db, Question, Category


class TriviaTestCase(unittest.TestCase):
    """This class represents the trivia test case"""

    def setUp(self):
        """Define test variables and initialize app."""
        self.app = create_app()
        self.client = self.app.test_client
        self.database_name = "trivia"
        self.database_path = "postgresql://postgres:theblackwatch@{}/{}".format('localhost:5432', self.database_name)
        setup_db(self.app, self.database_path)

        # binds the app to the current context
        with self.app.app_context():
            self.db = SQLAlchemy()
            self.db.init_app(self.app)
            # create all tables
            self.db.create_all()

    def tearDown(self):
        """Executed after reach test"""
        pass

    def test_questions_endpoint(self):
        response = self.client().get('/questions')
        self.assertEqual(response.status_code, 200)

    def test_categories_endpoint(self):
        response = self.client().get('/categories')
        self.assertEqual(response.status_code, 200)

    def test_category_questions_endpoint(self):
        response = self.client().get('/categories/1/questions')
        category = Category.query.get(int(1))
        data = json.loads(response.data)
        self.assertEqual(data.get('current_category'), category.type)
        all_questions_have_same_category = all(map(lambda x: x.get('category'), data.get('questions')))
        self.assertTrue(all_questions_have_same_category)

    def test_searching_questions(self):
        search_term = 'title'
        response = self.client().post('/questions', data=json.dumps({'searchTerm': search_term}))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        all_questions_have_search_term = all(map(lambda x: search_term in x.get('question'), data.get('questions')))
        self.assertTrue(all_questions_have_search_term)

    def test_quiz_endpoint(self):
        previous_questions = [1, 2, 3]
        category = "History"
        response = self.client().post('/quizzes', data=json.dumps({'previous_questions': previous_questions,
                                                                   'quiz_category': category}))

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        question_id = data.get('question').get('id')
        self.assertNotIn(previous_questions, [question_id])

    def test_create_question(self):
        question = {
            'question': 'Which anime constitute the "Big 3"?',
            'answer': 'Naruto, Bleach, One Piece',
            'category': '1',
            'difficulty': 1
        }

        response = self.client().post('/questions', json=question)
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)

    def test_invalid_data_create_question(self):
        question = {
            'question': 'Do you love udacity?',
            'answer': 'Yes i really do!',
            'difficulty': 1
        }
        # purposely posting a question with a missing parameter
        response = self.client().post('/questions', data=question)
        self.assertEqual(response.status_code, 400)

    def test_delete_question(self):
        # add a new question
        question = Question(question='Do you love udacity?', answer='Yes i really do!', category=1, difficulty=1)
        with self.app.app_context():
            self.db.session.add(question)
            self.db.session.commit()
            self.db.session.refresh(question)

        # delete the question just created
        response = self.client().delete(f'/questions/{question.id}')
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data.get('success'))

    def test_422_delete_question(self):
        # deletes a question that does not exist
        response = self.client().delete(f'/questions/{0}')
        self.assertEqual(response.status_code, 422)

    def test_invalid_endpoint(self):
        response = self.client().get('/not-a-real-endpoint')
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(data['message'], 'resource not found')


# Make the tests conveniently executable
if __name__ == "__main__":
    unittest.main()
