from django.urls import path
from apps.base.templatetags.menu_decorador import add_menu_name
from django.contrib.auth.decorators import login_required
from apps.surveys.views.hierarchy_view import HierarchyItemCreateView, HierarchyItemDeleteView, HierarchyItemListView, HierarchyItemUpdateView, hierarchy_item_create, hierarchy_item_delete, hierarchy_item_list, hierarchy_item_reorder, hierarchy_item_update
from apps.surveys.views.question_view import (
    QuestionCreateView,
    QuestionDeleteView,
    QuestionListView,
    QuestionUpdateView
    )
from apps.surveys.views.questionchoice_view import (
    QuestionChoiceCreateView,
    QuestionChoiceDeleteView,
    QuestionChoiceListView,
    QuestionChoiceReorderView,
    QuestionChoiceUpdateView
    )
from apps.surveys.views.response_view import SurveyResponseCreateView, SurveyThankYouView
from apps.surveys.views.survey_view import (
    SurveyCreateView,
    SurveyDeleteView,
    SurveyDetailView,
    SurveyExportView,
    SurveyListView,
    SurveyPDFExportView,
    SurveyPreviewView,
    SurveyPublishView,
    SurveyUnpublishView,
    SurveyUpdateView
    )
# from apps.surveys.views.survey_view import (
#     ResponseDetailView,
#     ResponseListView,
#     SurveyCreateView,
#     SurveyDashboardView,
#     SurveyDeleteView,
#     SurveyDetailView,
#     # SurveyExportView,
#     SurveyListView,
#     # SurveyPDFDownloadView,
#     # SurveyPDFExportView,
#     # SurveyPDFPreviewView,
#     # SurveyPreviewView,
#     SurveyPublishView,
#     # SurveyResponseCreateView,
#     SurveyThankYouView,
#     SurveyUnavailableView,
#     SurveyUnpublishView,
#     SurveyUpdateView
#     )

app_name = 'encuestas'

urlpatterns = [
    # Survey Management URLs
    path('surveys/', login_required(add_menu_name('LISTAR ENCUESTAS','checklist')(SurveyListView.as_view())), name='survey_list'),
    path('surveys/create/', SurveyCreateView.as_view(), name='survey_create'),
    path('surveys/<int:pk>/', SurveyDetailView.as_view(), name='survey_detail'),
    path('surveys/update/<int:pk>', SurveyUpdateView.as_view(), name='survey_update'),
    path('surveys/<int:pk>/delete/', SurveyDeleteView.as_view(), name='survey_delete'),
    path('surveys/<int:pk>/publish/', SurveyPublishView.as_view(), name='survey_publish'),
    path('surveys/<int:pk>/unpublish/', SurveyUnpublishView.as_view(), name='survey_unpublish'),
    path('thank-you/', SurveyThankYouView.as_view(), name='survey_thank_you'),
    path('surveys/<int:pk>/preview/', SurveyPreviewView.as_view(), name='survey_preview'),
    path('surveys/<int:pk>/export/', SurveyExportView.as_view(), name='survey_export'),
    path('surveys/<int:pk>/export/pdf/', SurveyPDFExportView.as_view(), name='survey_pdf_export'),
    # path('surveys/<int:pk>/dashboard/', SurveyDashboardView.as_view(), name='survey_dashboard'),
    # path('surveys/<int:pk>/pdf/', SurveyPDFExportView.as_view(), name='survey_pdf'),
    # path('surveys/<int:pk>/pdf/preview/', SurveyPDFPreviewView.as_view(), name='survey_pdf_preview'),
    # path('surveys/<int:pk>/pdf/download/', SurveyPDFDownloadView.as_view(), name='survey_pdf_download'),
    # organizar las views
    path('surveys/<int:pk>/responses/', SurveyDetailView.as_view(), name='survey_responses'),
    # path('surveys/<int:pk>/responses/', SurveyExportView.as_view(), name='surveyresponse_export'),
    
    # QuestionChoice Management URLs
    path('questions/<int:question_id>/choices/', 
        QuestionChoiceListView.as_view(), 
        name='choice_list'),
    path('questions/<int:question_id>/choices/add/',
        QuestionChoiceCreateView.as_view(), 
        name='choice_create'),
    path('choices/<int:pk>/edit/', 
        QuestionChoiceUpdateView.as_view(), 
        name='choice_update'),
    path('choices/<int:pk>/delete/', 
        QuestionChoiceDeleteView.as_view(), 
        name='choice_delete'),
    path('api/questions/choices/reorder/', 
        QuestionChoiceReorderView.as_view(), 
        name='choice_reorder'),

    # HierarchyItem Management URLs
    # path('questions/<int:question_id>/hierarchy-items/', 
    #      HierarchyItemListView, 
    #      name='hierarchy_item_list'),

    # Question Management URLs
    path('surveys/<int:survey_id>/questions/', QuestionListView.as_view(), name='question_list'),
    path('surveys/<int:survey_id>/questions/create/', QuestionCreateView.as_view(), name='question_create'),
    path('questions/<int:pk>/update/', QuestionUpdateView.as_view(), name='question_update'),
    path('questions/<int:pk>/delete/', QuestionDeleteView.as_view(), name='question_delete'),
    
    # # Public Survey Response URLs
    path('respond/<int:survey_id>/', SurveyResponseCreateView.as_view(), name='survey_respond'),
    # path('unavailable/', SurveyUnavailableView.as_view(), name='survey_unavailable'),
    
    # URLs para vistas basadas en clase (preferidas)
    path('questions/<int:question_id>/hierarchy-items/', 
         HierarchyItemListView.as_view(), 
         name='hierarchy_item_list'),
    
    path('questions/<int:question_id>/hierarchy-items/create/', 
         HierarchyItemCreateView.as_view(), 
         name='hierarchy_item_create'),
    
    path('questions/<int:question_id>/hierarchy-items/<int:item_id>/update/', 
         HierarchyItemUpdateView.as_view(), 
         name='hierarchy_item_update'),
    
    path('questions/<int:question_id>/hierarchy-items/<int:item_id>/delete/', 
         HierarchyItemDeleteView.as_view(), 
         name='hierarchy_item_delete'),
    

    # Hierarchy Item URLs
    # path('questions/<int:question_id>/hierarchy-items/', hierarchy_item_list, name='hierarchy_item_list'),
    # path('questions/<int:question_id>/hierarchy-items/create/', hierarchy_item_create, name='hierarchy_item_create'),
    # path('hierarchy-items/<int:item_id>/update/', hierarchy_item_update, name='hierarchy_item_update'),
    # path('hierarchy-items/<int:item_id>/delete/', hierarchy_item_delete, name='hierarchy_item_delete'),
    # path('questions/<int:question_id>/hierarchy-items/reorder/', hierarchy_item_reorder, name='hierarchy_item_reorder'),

    # API URLs
    # path('api/surveys/questions/reorder/', reorder_questions, name='api_reorder_questions'),
    # path('api/questions/<int:question_id>/hierarchy-items/', get_hierarchy_items, name='api_get_hierarchy_items'),
    # path('api/questions/<int:question_id>/hierarchy-items/create/', create_hierarchy_item, name='api_create_hierarchy_item'),
    # path('api/hierarchy-items/<int:item_id>/update/', update_hierarchy_item, name='api_update_hierarchy_item'),
    # path('api/hierarchy-items/<int:item_id>/delete/', delete_hierarchy_item, name='api_delete_hierarchy_item'),
    # path('api/questions/<int:question_id>/hierarchy-items/reorder/', reorder_hierarchy_items, name='api_reorder_hierarchy_items'),

    # API URLs
    # path('api/surveys/questions/reorder/', reorder_questions, name='api_reorder_questions'),
    # path('api/questions/<int:question_id>/hierarchy-items/', get_hierarchy_items, name='api_get_hierarchy_items'),
    path('api/questions/<int:question_id>/hierarchy-items/create/', hierarchy_item_create, name='api_create_hierarchy_item'),
    path('api/hierarchy-items/<int:item_id>/update/', hierarchy_item_update, name='api_update_hierarchy_item'),
    path('api/hierarchy-items/<int:item_id>/delete/', hierarchy_item_delete, name='api_delete_hierarchy_item'),
    path('api/questions/<int:question_id>/hierarchy-items/reorder/', hierarchy_item_reorder, name='hierarchy_item_reorder'),

    # # Response Management URLs
    # path('surveys/<int:survey_id>/responses/', ResponseListView.as_view(), name='response_list'),
    # path('responses/<int:pk>/', ResponseDetailView.as_view(), name='response_detail'),
    
    # # Period Management URLs
    # path('periods/', PeriodListView.as_view(), name='period_list'),
    # path('periods/create/', PeriodCreateView.as_view(), name='period_create'),
    # path('periods/<int:pk>/update/', PeriodUpdateView.as_view(), name='period_update'),
    # path('periods/<int:pk>/delete/', PeriodDeleteView.as_view(), name='period_delete'),
    
    # # Indicator Management URLs
    # path('indicators/', IndicatorListView.as_view(), name='indicator_list'),
    # path('indicators/calculate/', CalculateIndicatorsView.as_view(), name='calculate_indicators'),
]