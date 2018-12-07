from rest_framework import permissions
from query.models import Query, QuerySharedUsers


class IsOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True

        query = Query.objects.get(id=obj.id)
        return query.owner == request.user

class IsSharedOwner(permissions.BasePermission):
	def has_object_permission(self, request, view, obj):
		if request.user.is_superuser:
			return True

		instance = QuerySharedUsers.objects.get(query=obj)
		shared_users = instance.person

		if obj.owner == request.owner:
			return True
		else:
			if request.user in shared_users:
				return True
			else:
				return False