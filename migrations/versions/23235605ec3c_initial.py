"""initial

Revision ID: 23235605ec3c
Revises: 
Create Date: 2024-01-11 10:58:56.553339

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '23235605ec3c'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('courses',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_table('secrets',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('token', sa.String(length=1024), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('token')
    )
    op.create_table('subjects',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('course_number', sa.String(length=16), nullable=False),
    sa.Column('lec_hours', sa.Integer(), nullable=False),
    sa.Column('lab_hours', sa.Integer(), nullable=False),
    sa.Column('units', sa.Integer(), nullable=False),
    sa.Column('year_level', sa.String(length=64), nullable=False),
    sa.Column('semester', sa.String(length=64), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('course_number'),
    sa.UniqueConstraint('title')
    )
    op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('email', sa.String(length=255), nullable=False),
    sa.Column('password', sa.LargeBinary(), nullable=False),
    sa.Column('role', sa.String(length=16), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email')
    )
    op.create_table('course_subject',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('course_id', sa.Integer(), nullable=False),
    sa.Column('subject_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['course_id'], ['courses.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['subject_id'], ['subjects.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('course_id', 'subject_id')
    )
    op.create_table('students',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('image_filename', sa.String(length=255), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('course_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['course_id'], ['courses.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('teachers',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('schedules',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('school_year', sa.String(length=255), nullable=False),
    sa.Column('semester', sa.String(length=255), nullable=False),
    sa.Column('day', sa.String(length=255), nullable=False),
    sa.Column('year_level', sa.String(length=255), nullable=False),
    sa.Column('course_id', sa.Integer(), nullable=False),
    sa.Column('teacher_id', sa.Integer(), nullable=False),
    sa.Column('subject_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['course_id'], ['courses.id'], ),
    sa.ForeignKeyConstraint(['subject_id'], ['subjects.id'], ),
    sa.ForeignKeyConstraint(['teacher_id'], ['teachers.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('teacher_id', 'subject_id')
    )
    op.create_table('attendances',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('schedule_id', sa.Integer(), nullable=True),
    sa.Column('student_id', sa.Integer(), nullable=True),
    sa.Column('time_in', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['schedule_id'], ['schedules.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['student_id'], ['students.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('schedule_student',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('schedule_id', sa.Integer(), nullable=False),
    sa.Column('student_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['schedule_id'], ['schedules.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['student_id'], ['students.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('schedule_id', 'student_id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('schedule_student')
    op.drop_table('attendances')
    op.drop_table('schedules')
    op.drop_table('teachers')
    op.drop_table('students')
    op.drop_table('course_subject')
    op.drop_table('users')
    op.drop_table('subjects')
    op.drop_table('secrets')
    op.drop_table('courses')
    # ### end Alembic commands ###