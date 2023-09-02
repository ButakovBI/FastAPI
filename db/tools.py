# import os
#
# from sqlalchemy import Column, Integer, String, Boolean, create_engine
# from sqlalchemy.orm import declarative_base, sessionmaker
#
# engine = create_engine("sqlite:///db.sqlite3")
#
#
# class Base(declarative_base):
#     pass
#
#
# class Todo(Base):
#     __tablename__ = "todo"
#     id = Column(Integer, primary_key=True)
#     title = Column(String)
#     description = Column(String)
#     completed = Column(Boolean, default=False)
#
#
# class SqliteTools:
#     session = sessionmaker(autoflush=False, bind=engine)
#
#     @classmethod
#     def check_exists_db(cls):
#         if not os.path.exists("db.sqlite3"):
#             Base.metadata.create_all(bind=engine)
#
#     @classmethod
#     def add_todo(cls, title, description):
#         todo = Todo(title=title, description=description)
#         with cls.session(autoflush=False, bind=engine) as db:
#             db.add(todo)
#             db.commit()
#             todo = db.query(Todo).get(todo.id)
#         return todo
#
#     @classmethod
#     def get_todo_by_id(cls, id):
#         with cls.session(autoflush=False, bind=engine) as db:
#             todo = db.query(Todo).get(id)
#         return todo
#
#     @classmethod
#     def delete_todo_by_id(cls, id):
#         with cls.session(autoflush=False, bind=engine) as db:
#             todo = db.query(Todo).get(id)
#             if todo:
#                 db.delete(todo)
#                 db.commit()
#                 return True
#
#     @classmethod
#     def update_todo_by_id(cls, id, title, description, completed):
#         with cls.session(autoflush=False, bind=engine) as db:
#             todo = db.query(Todo).get(id)
#             todo.title = title
#             todo.description = description
#             todo.completed = completed
#             db.commit()
#             todo = db.query(Todo).get(todo.id)
#         return todo