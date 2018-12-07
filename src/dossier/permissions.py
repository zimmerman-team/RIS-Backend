from rest_framework import permissions
from dossier.models import DossierSharedUsers

SAFE_METHODS = ('GET', 'HEAD', 'OPTIONS')

def get_permission(obj, request):
    if obj.owner == request.user:
        return True
    else:
        try:
            shared_user = DossierSharedUsers.objects.get(dossier=obj, person=request.user)
            permission = shared_user.permission
            if request.method in SAFE_METHODS:
                return True
            else:
                if permission == 'edit':
                    return True
                else:
                    return False
        except Exception:
            return False


class DossierPermission(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if obj.accessibility == 'Public' and obj.is_verified == True:
            return True
        else:
            return get_permission(obj, request)


class ContentPermission(permissions.BasePermission):
    message = "U hebt geen toestemming voor deze actie"
    def has_object_permission(self, request, view, obj):
        print "here"
        _obj = obj.dossier
        return get_permission(_obj, request)


class IsOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True

        return True


class IsSharedOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True

        instance = DossierSharedUsers.objects.get(query=obj)
        shared_users = instance.person

        if obj.owner == request.owner:
            return True
        else:
            if request.user in shared_users:
                return True
            else:
                return False