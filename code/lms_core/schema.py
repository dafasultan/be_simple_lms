from ninja import Schema
from typing import Optional
from datetime import datetime

from django.contrib.auth.models import User

class UserOut(Schema):
    id: int
    email: str
    first_name: str
    last_name: str


class CourseSchemaOut(Schema):
    id: int
    name: str
    description: str
    price: int
    image : Optional[str]
    teacher: UserOut
    created_at: datetime
    updated_at: datetime

class CourseMemberOut(Schema):
    id: int 
    course_id: CourseSchemaOut
    user_id: UserOut
    roles: str
    # created_at: datetime


class CourseSchemaIn(Schema):
    name: str
    description: str
    price: int


class CourseContentMini(Schema):
    id: int
    name: str
    description: str
    course_id: CourseSchemaOut
    created_at: datetime
    updated_at: datetime


class CourseContentFull(Schema):
    id: int
    name: str
    description: str
    video_url: Optional[str]
    file_attachment: Optional[str]
    course_id: CourseSchemaOut
    created_at: datetime
    updated_at: datetime

class CourseCommentOut(Schema):
    id: int
    content_id: CourseContentMini
    member_id: CourseMemberOut
    comment: str
    created_at: datetime
    updated_at: datetime

class CourseCommentIn(Schema):
    comment: str


class CourseFeedbackCreateSchema(Schema):
    course_id: int
    rating: int
    feedback: str = None
    created_by: str
    show_date: datetime

    class Config:
        orm_mode = True

class CourseFeedbackResponseSchema(Schema):
    id: int
    course_id: int
    rating: int
    feedback: str
    created_at: datetime
    updated_at: datetime

class FeedbackUpdateSchema(Schema):
    rating: int
    feedback: str

class CategoryCreate(Schema):
    name: str


class CourseCreateSchema(Schema):
    name: str
    description: str
    price: int
    teacher_id: Optional[int] = None
    category_id: Optional[int] = None


class CourseUpdateSchema(Schema):
    name: Optional[str]
    description: Optional[str]
    price: Optional[int]
    teacher_id: Optional[int]
    category_id: Optional[int]


class CompletionTrackingCreateSchema(Schema):
    student_username: str  
    content_id: int
    course_id: int
    
    
class CompletionTrackingResponseSchema(Schema):
    content_name: str  
    completed_at: datetime  
    completed: bool  
    
class PublishContentSchema(Schema):
    username: str
    is_published: bool
    
    
class CourseContentUpdateSchema(Schema):
    name: Optional[str] = None
    description: Optional[str] = None
    video_url: Optional[str] = None
    file_attachment: Optional[str] = None
    course_id: Optional[int] = None
    parent_id: Optional[int] = None
    teacher_id: Optional[int] = None
    is_published: Optional[bool] = None


class GetCourseContentSchema(Schema):
    username: str 
    
class UserRoleSchema(Schema):
    username: str  
    is_teacher: Optional[bool] = None