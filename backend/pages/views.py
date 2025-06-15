from django.shortcuts import render
from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from accounts.models import User, Page, UserPagePermission, Comment
from accounts.serializers import CommentSerializer
from accounts.views import user_has_permission

# List of the 10 predefined pages
PAGE_NAMES = [
    'products_list',
    'marketing_list', 
    'order_list',
    'media_plans',
    'offer_pricing_skus',
    'clients',
    'suppliers',
    'customer_support',
    'sales_reports',
    'finance_accounting'
]

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def page_detail(request, page_name):
    """
    Get page details and comments for a specific page
    """
    if page_name not in PAGE_NAMES:
        return Response(
            {"error": "Page not found"}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Check if user has view permission for this page
    if not user_has_permission(request.user, page_name, "view"):
        return Response(
            {"error": "You do not have permission to view this page"},
            status=status.HTTP_403_FORBIDDEN,
        )
    
    # Get page details
    try:
        page = Page.objects.get(name=page_name)
    except Page.DoesNotExist:
        # Create the page if it doesn't exist
        page = Page.objects.create(
            name=page_name,
            description=f"Page for {page_name.replace('_', ' ').title()}",
            url=f"/{page_name.replace('_', '-')}"
        )
    
    # Get comments for this page
    comments = Comment.objects.filter(page_name=page_name, is_deleted=False)
    comment_serializer = CommentSerializer(comments, many=True)
    
    return Response({
        "page": {
            "id": page.id,
            "name": page.name,
            "description": page.description,
            "url": page.url
        },
        "comments": comment_serializer.data,
        "user_permissions": {
            "can_view": user_has_permission(request.user, page_name, "view"),
            "can_edit": user_has_permission(request.user, page_name, "edit"),
            "can_create": user_has_permission(request.user, page_name, "create"),
            "can_delete": user_has_permission(request.user, page_name, "delete"),
        }
    })

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def pages_list(request):
    """
    Get list of all pages with user permissions
    """
    pages_data = []
    
    for page_name in PAGE_NAMES:
        try:
            page = Page.objects.get(name=page_name)
        except Page.DoesNotExist:
            # Create the page if it doesn't exist
            page = Page.objects.create(
                name=page_name,
                description=f"Page for {page_name.replace('_', ' ').title()}",
                url=f"/{page_name.replace('_', '-')}"
            )
        
        pages_data.append({
            "id": page.id,
            "name": page.name,
            "description": page.description,
            "url": page.url,
            "user_permissions": {
                "can_view": user_has_permission(request.user, page_name, "view"),
                "can_edit": user_has_permission(request.user, page_name, "edit"),
                "can_create": user_has_permission(request.user, page_name, "create"),
                "can_delete": user_has_permission(request.user, page_name, "delete"),
            }
        })
    
    return Response(pages_data)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def add_comment(request, page_name):
    """
    Add a new comment to a page
    """
    if page_name not in PAGE_NAMES:
        return Response(
            {"error": "Page not found"}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Check if user has create permission for this page
    if not user_has_permission(request.user, page_name, "create"):
        return Response(
            {"error": "You do not have permission to create comments on this page"},
            status=status.HTTP_403_FORBIDDEN,
        )
    
    serializer = CommentSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(user=request.user, page_name=page_name)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PUT', 'DELETE'])
@permission_classes([permissions.IsAuthenticated])
def comment_detail(request, page_name, comment_id):
    """
    Update or delete a comment
    """
    if page_name not in PAGE_NAMES:
        return Response(
            {"error": "Page not found"}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    comment = get_object_or_404(Comment, id=comment_id, page_name=page_name, is_deleted=False)
    
    if request.method == 'PUT':
        # Check if user has edit permission for this page
        if not user_has_permission(request.user, page_name, "edit"):
            return Response(
                {"error": "You do not have permission to edit comments on this page"},
                status=status.HTTP_403_FORBIDDEN,
            )
        
        serializer = CommentSerializer(comment, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save(modified_by=request.user)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        # Check if user has delete permission for this page
        if not user_has_permission(request.user, page_name, "delete"):
            return Response(
                {"error": "You do not have permission to delete comments on this page"},
                status=status.HTTP_403_FORBIDDEN,
            )
        
        # Soft delete
        comment.is_deleted = True
        comment.save()
        
        return Response({"message": "Comment deleted successfully"})
