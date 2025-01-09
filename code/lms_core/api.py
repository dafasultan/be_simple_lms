from ninja import NinjaAPI, UploadedFile, File, Form
from ninja.responses import Response
from lms_core.schema import CourseSchemaOut, CourseMemberOut, CourseSchemaIn
from lms_core.schema import CourseContentMini, CourseContentFull
from lms_core.schema import CourseCommentOut, CourseCommentIn
from lms_core.schema import CourseFeedbackCreateSchema, CourseFeedbackResponseSchema, FeedbackUpdateSchema
from lms_core.schema import CategoryCreate, CourseCreateSchema, CourseUpdateSchema
from lms_core.schema import CompletionTrackingCreateSchema, CompletionTrackingResponseSchema, CourseContentUpdateSchema
from lms_core.schema import PublishContentSchema, GetCourseContentSchema, UserRoleSchema
from lms_core.models import Course, CourseMember, CourseContent, Comment, CompletionTracking
from lms_core.models import Profile, CourseFeedback, CourseCategory
from ninja_simple_jwt.auth.views.api import mobile_auth_router
from ninja_simple_jwt.auth.ninja_auth import HttpJwtAuth
from ninja.pagination import paginate, PageNumberPagination

from django.contrib.auth.models import User
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
import json


apiv1 = NinjaAPI()
apiv1.add_router("/auth/", mobile_auth_router)
apiAuth = HttpJwtAuth()

@apiv1.get("/hello")
def hello(request):
    return "Hello World"

# - paginate list_courses
@apiv1.get("/courses", response=list[CourseSchemaOut])
@paginate(PageNumberPagination, page_size=10)
def list_courses(request):
    courses = Course.objects.select_related('teacher').all()
    return courses

# - my courses
@apiv1.get("/mycourses", auth=apiAuth, response=list[CourseMemberOut])
def my_courses(request):
    user = User.objects.get(id=request.user.id)
    courses = CourseMember.objects.select_related('user_id', 'course_id').filter(user_id=user)
    return courses

# - create course
@apiv1.post("/courses", auth=apiAuth, response={201:CourseSchemaOut})
def create_course(request, data: Form[CourseSchemaIn], image: UploadedFile = File(None)):
    user = User.objects.get(id=request.user.id)
    course = Course(
        name=data.name,
        description=data.description,
        price=data.price,
        image=image,
        teacher=user
    )

    if image:
        course.image.save(image.name, image)

    course.save()
    return 201, course

# - update course
@apiv1.post("/courses/{course_id}", auth=apiAuth, response=CourseSchemaOut)
def update_course(request, course_id: int, data: Form[CourseSchemaIn], image: UploadedFile = File(None)):
    if request.user.id != Course.objects.get(id=course_id).teacher.id:
        message = {"error": "Anda tidak diijinkan update course ini"}
        return Response(message, status=401)
    
    course = Course.objects.get(id=course_id)
    course.name = data.name
    course.description = data.description
    course.price = data.price
    if image:
        course.image.save(image.name, image)
    course.save()
    return course

# - detail course
@apiv1.get("/courses/{course_id}", response=CourseSchemaOut)
def detail_course(request, course_id: int):
    course = Course.objects.select_related('teacher').get(id=course_id)
    return course

# - list content course
@apiv1.get("/courses/{course_id}/contents", response=list[CourseContentMini])
def list_content_course(request, course_id: int):
    contents = CourseContent.objects.filter(course_id=course_id)
    return contents

# - detail content course
@apiv1.get("/courses/{course_id}/contents/{content_id}", response=CourseContentFull)
def detail_content_course(request, course_id: int, content_id: int):
    content = CourseContent.objects.get(id=content_id)
    return content

# - enroll course
@apiv1.post("/courses/{course_id}/enroll", auth=apiAuth, response=CourseMemberOut)
def enroll_course(request, course_id: int):
    user = User.objects.get(id=request.user.id)
    course = Course.objects.get(id=course_id)
    course_member = CourseMember(course_id=course, user_id=user, roles="std")
    course_member.save()
    # print(course_member)
    return course_member

# - list content comment
@apiv1.get("/contents/{content_id}/comments", auth=apiAuth, response=list[CourseContentMini])
def list_content_comment(request, content_id: int):
    comments = CourseContent.objects.filter(course_id=content_id)
    return comments

# - create content comment
@apiv1.post("/contents/{content_id}/comments", auth=apiAuth, response={201: CourseCommentOut})
def create_content_comment(request, content_id: int, data: CourseCommentIn):
    user = User.objects.get(id=request.user.id)
    content = CourseContent.objects.get(id=content_id)

    if not content.course_id.is_member(user):
        message =  {"error": "You are not authorized to create comment in this content"}
        return Response(message, status=401)
    
    member = CourseMember.objects.get(course_id=content.course_id, user_id=user)
    
    comment = Comment(
        content_id=content,
        member_id=member,
        comment=data.comment
    )
    comment.save()
    return 201, comment

# - delete content comment
@apiv1.delete("/comments/{comment_id}", auth=apiAuth)
def delete_comment(request, comment_id: int):
    comment = Comment.objects.get(id=comment_id)
    if comment.member_id.user_id.id != request.user.id:
        return {"error": "You are not authorized to delete this comment"}
    comment.delete()
    return {"message": "Comment deleted"}   




# New
@apiv1.post("/register/")
def register_user(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        full_name = data.get('full_name')
        phone_number = data.get('phone_number', '')  
        description = data.get('description', '')  
        profile_picture = data.get('profile_picture', None)  
        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=full_name.split()[0],  last_name=" ".join(full_name.split()[1:]),  )

            profile = Profile.objects.create(
                user=user,
                phone_number=phone_number,
                description=description,
                profile_picture=profile_picture
            )
            return JsonResponse({"message": "Registrasi berhasil!"}, status=201)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
    else:
        return JsonResponse({"error": "Gunakan POST untuk mendaftar."}, status=400)

@apiv1.post("/feedbacks/", response=CourseFeedbackResponseSchema)
def create_feedback(request, data: CourseFeedbackCreateSchema):
    try:
        student = User.objects.get(username=data.created_by)
    except User.DoesNotExist:
        return JsonResponse({"detail": "User not found"}, status=404)
    if not student.is_authenticated:
        return JsonResponse({"detail": "Only authenticated students can provide feedback"}, status=403)
    course = get_object_or_404(Course, id=data.course_id)
    if CourseFeedback.objects.filter(course=course, student=student).exists():
        return JsonResponse({"detail": "You have already given feedback for this course"}, status=400)
    
    feedback = CourseFeedback.objects.create(
        course=course,
        student=student,
        rating=data.rating,
        feedback=data.feedback,
    )

    return JsonResponse({
        "message": "Feedback Added",
        "feedback": {
            "id": feedback.id,
            "course_id": feedback.course.id,
            "student_id": feedback.student.id,
            "rating": feedback.rating,
            "feedback": feedback.feedback,
            "created_at": feedback.created_at,
            "updated_at": feedback.updated_at,}
    }, status=201)
    
@apiv1.get("/show-feedback/", auth=apiAuth)
def show_feedback(request, course_id: int):
    course = get_object_or_404(Course, id=course_id)
    feedbacks = CourseFeedback.objects.filter(course=course)
    feedback_data = []
    for feedback in feedbacks:
        feedback_data.append({
            "id": feedback.id,
            "course_id": feedback.course.id,
            "student_id": feedback.student.id,
            "rating": feedback.rating,
            "feedback": feedback.feedback,
            "created_at": feedback.created_at,
            "updated_at": feedback.updated_at,
        })

    return JsonResponse({
        "message": "Showing Feedbacks",
        "course_id": course.id,
        "feedbacks": feedback_data
    }, status=200)

@apiv1.put("/edit-feedback/{feedback_id}", auth=apiAuth)
def edit_feedback(request, feedback_id: int, data: FeedbackUpdateSchema):
    feedback = get_object_or_404(CourseFeedback, id=feedback_id)
    if request.user.id != feedback.student.id:
        return JsonResponse({
            "detail": "Only the student who created this feedback can edit it.",
            }, status=403) 
        
    feedback.rating = data.rating
    feedback.feedback = data.feedback
    feedback.save()

    return JsonResponse({
        "message": "Feedback updated successfully",
        "feedback": {
            "id": feedback.id,
            "course_id": feedback.course.id,
            "student_id": feedback.student.id,
            "rating": feedback.rating,
            "feedback": feedback.feedback,
            "updated_at": feedback.updated_at,
        }
    }, status=200)
    
    
@apiv1.delete("/delete-feedback/", auth=apiAuth)
def delete_feedback(request, student_id: int, feedback_id: int):
    student = get_object_or_404(User, id=student_id)
    feedback = CourseFeedback.objects.filter(student=student, id=feedback_id).first()
    if not feedback:
        return JsonResponse({"error": "Feedback not found for this student."}, status=404)
    feedback.delete()

    return JsonResponse({"message": "Feedback successfully deleted."}, status=200)

@apiv1.post("/add-category/", auth=apiAuth)
def add_category(request, data: CategoryCreate):
    category = CourseCategory.objects.create(name=data.name)
    return JsonResponse({
        "message": "Category added successfully.",
        "category_id": category.id
    })
    
@apiv1.get("/show-categories/", auth=apiAuth)
def show_categories(request):
    categories = CourseCategory.objects.all()
    category_list = [{"id": category.id, "name": category.name} for category in categories]
    return JsonResponse({"categories": category_list}, status=200)

@apiv1.delete("/delete-category/{category_id}/", auth=apiAuth)
def delete_category(request, category_id: int):
    category = get_object_or_404(CourseCategory, id=category_id)
    category.delete()
    return JsonResponse({"message": "Category deleted successfully."}, status=200)


@apiv1.post("/create-course/", auth=apiAuth)
def create_course(request, data: CourseCreateSchema):
    teacher = None
    if data.teacher_id:
        teacher = get_object_or_404(User, id=data.teacher_id)
    category = None
    if data.category_id:
        category = get_object_or_404(CourseCategory, id=data.category_id)
    
    course = Course.objects.create(
        name=data.name,
        description=data.description,
        price=data.price,
        teacher=teacher,  
        category=category,
    )
    
    return JsonResponse({
        "message": "Course created successfully",
        "course_id": course.id,
        "category_id": course.category.id if course.category else None,
        "teacher_id": course.teacher.id if course.teacher else None  # Include teacher_id in response
    }, status=201)


@apiv1.put("/update-course/{course_id}/")
def update_course(request, course_id: int, data: CourseUpdateSchema):
    course = get_object_or_404(Course, id=course_id)
    if data.name:
        course.name = data.name
    if data.description:
        course.description = data.description
    if data.price is not None:  
        course.price = data.price
    if data.teacher_id:
        teacher = get_object_or_404(User, id=data.teacher_id)
        course.teacher = teacher
    if data.category_id:
        category = get_object_or_404(CourseCategory, id=data.category_id)
        course.category = category
    
    course.save()
    
    return JsonResponse({
        "message": "Course updated successfully",
        "course_id": course.id,
        "category_id": course.category.id if course.category else None,
        "teacher_id": course.teacher.id if course.teacher else None  
    }, status=200)


@apiv1.post("/add-completion/", auth=apiAuth)
def add_completion_tracking(request, data: CompletionTrackingCreateSchema):
    student_username = data.student_username  
    try:
        student = User.objects.get(username=student_username)
    except User.DoesNotExist:
        return JsonResponse({"detail": "User not found"}, status=404)

    content = get_object_or_404(CourseContent, id=data.content_id)

    completion, created = CompletionTracking.objects.update_or_create(
        student=student,
        content=content,
        defaults={'completed': True, 'completed_at': timezone.now()}
    )

    return JsonResponse({
        "student_username": student.username,
        "content_id": content.id,
        "completed": completion.completed,
        "completed_at": completion.completed_at,
    }, status=200)

@apiv1.get("/show-completion/", auth=apiAuth, response=CompletionTrackingResponseSchema)
def show_completion(request, course_id: int):
    course = get_object_or_404(Course, id=course_id)
    course_contents = CourseContent.objects.filter(course_id=course.id)

    completions = CompletionTracking.objects.filter(content__in=course_contents)

    completion_data = []
    for completion in completions:
        completion_data.append({
            "student_id": completion.student.id,
            "student_username": completion.student.username,
            "content_id": completion.content.id,
            "content_name": completion.content.name,
            "completed": completion.completed,
            "completed_at": completion.completed_at,
        })

    return JsonResponse({
        "course_id": course.id,
        "completions": completion_data
    }, status=200)

@apiv1.delete("/delete-completion/", auth=apiAuth)
def delete_completion(request, student_id: int, content_id: int):
    student = get_object_or_404(User, id=student_id)
    completion = CompletionTracking.objects.filter(student=student, content_id=content_id).first()
    
    if not completion:
        return JsonResponse({"error": "Completion not found for this student and content."}, status=404)

    completion.delete()
    
    return JsonResponse({"message": "Completion successfully deleted."}, status=200)

@apiv1.put("/update-content/{content_id}/", auth=apiAuth)
def update_course_content(request, content_id: int, data: CourseContentUpdateSchema):
    course_content = get_object_or_404(CourseContent, id=content_id)
    
    if data.name is not None:
        course_content.name = data.name
    if data.description is not None:
        course_content.description = data.description
    if data.video_url is not None:
        course_content.video_url = data.video_url
    if data.file_attachment is not None:
        course_content.file_attachment = data.file_attachment
    if data.course_id is not None:
        course_content.course_id = get_object_or_404(Course, id=data.course_id)
    if data.parent_id is not None:
        course_content.parent_id = get_object_or_404(CourseContent, id=data.parent_id)
    if data.teacher_id is not None:
        course_content.teacher = get_object_or_404(User, id=data.teacher_id)

    course_content.save()

    return JsonResponse({
        "message": "Course content updated successfully",
        "content_id": course_content.id
    }, status=200)

@apiv1.put("/publish-content/{content_id}/", auth=apiAuth)
def publish_content(request, content_id: int, data: PublishContentSchema):
    course_content = get_object_or_404(CourseContent, id=content_id)

    user = get_object_or_404(User, username=data.username)
    
    if user != course_content.teacher:
        return JsonResponse({"message": "You are not authorized to perform this action."}, status=403)

    course_content.is_published = data.is_published
    course_content.save()

    return JsonResponse({
        "message": "Course content publication status updated successfully",
        "is_published": course_content.is_published
    }, status=200)


@apiv1.post("/course-content/{course_id}/", auth=apiAuth)
def get_course_content(request, course_id: int, data: GetCourseContentSchema):
    username = data.username
    
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return JsonResponse({"message": "User not found"}, status=404)

    try:
        profile = Profile.objects.get(user=user)
        is_teacher = profile.role == 'teacher'  
    except Profile.DoesNotExist:
        is_teacher = False

    if is_teacher:
        course_contents = CourseContent.objects.filter(course_id=course_id)
    else:
        course_contents = CourseContent.objects.filter(course_id=course_id, is_published=True)

    contents_data = []
    for content in course_contents:
        contents_data.append({
            "name": content.name,
            "description": content.description,
            "video_url": content.video_url,
            "file_attachment": content.file_attachment.url if content.file_attachment else None,
            "is_published": content.is_published,
        })

    return JsonResponse({
        "message": "Course content fetched successfully",
        "contents": contents_data
    }, status=200)
