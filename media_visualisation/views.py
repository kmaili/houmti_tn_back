from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.conf import settings
from django.http import FileResponse
import os
from core.authentication import APIKeyAuthentication


class SecureMediaView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        file_name = request.GET.get('file_name')
        if not file_name:
            return Response({"detail": "File name is required"}, status=400)
        
        file_name = file_name.replace(settings.MEDIA_URL, "")
        print(file_name)
        file_path = os.path.join(settings.MEDIA_ROOT, file_name)
        print(file_path)
        if not os.path.exists(file_path):
            return Response({"detail": "Not found"}, status=404)
        return FileResponse(open(file_path, 'rb'))