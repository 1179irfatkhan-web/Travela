from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.contrib import messages
from django.db import models
from .models import UserRegistration, Package, Booking, PackageDayPlan, DayPhoto, PassengerDetail,Feedback, ContactMessage


@admin.register(UserRegistration)
class UserRegistrationAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'email',
        'phone',
        'aadhar_number',  # Add this
        'has_profile_photo',
        'city',
        'state',
        'booking_count',
        'total_spent',
        'created_at',
    )
    list_display_links = ('name', 'email')
    search_fields = ('name', 'email', 'phone', 'city','aadhar_number')
    list_filter = ('city', 'state', 'created_at')
    list_per_page = 25
    def has_profile_photo(self, obj):
        if obj.profile_photo:
            return format_html('<img src="{}" width="50" height="50" style="border-radius: 50%;">', obj.profile_photo.url)
        return "No Photo"
    has_profile_photo.short_description = 'Photo'

    def booking_count(self, obj):
        count = Booking.objects.filter(user=obj).count()
        # Correct URL pattern for admin
        url = reverse('admin:Tours_booking_changelist') + f'?user__id={obj.id}'
        return format_html('<a href="{}" style="font-weight: bold;">{} Bookings</a>', url, count)

    booking_count.short_description = 'Total Bookings'

    def total_spent(self, obj):
        total = Booking.objects.filter(user=obj).aggregate(total=models.Sum('total_price'))['total'] or 0
        return format_html('<span style="color: #28a745; font-weight: bold;">₹{}</span>', total)

    total_spent.short_description = 'Total Spent'

    def get_profile_photo_url(self):
        if self.profile_photo:
            return self.profile_photo.url
        return '/static/img/default-avatar.jpg'

# Use TabularInline for photos because it is compact
class DayPhotoInline(admin.TabularInline):
    model = DayPhoto
    extra = 1

@admin.register(PackageDayPlan)
class PackageDayPlanAdmin(admin.ModelAdmin):
    inlines = [DayPhotoInline]
    list_display = ('day_number', 'title', 'package')
    list_filter = ('package',)

# Use StackedInline for DayPlans because they have large text descriptions
class DayPlanInline(admin.StackedInline):
    model = PackageDayPlan
    extra = 1

@admin.register(Package)
class PackageAdmin(admin.ModelAdmin):
    inlines = [DayPlanInline]
    list_display = (
        'id',
        'title',
        'source_city',
        'location',
        'category',
        'base_price',
        'duration',
        'available_seats',
        'max_persons',
        'booking_count',
        'revenue_generated',
        'triptime_display',
    )
    list_display_links = ('title',)
    list_filter = ('category', 'location', 'duration')
    search_fields = ('title', 'location', 'source_city', 'description')
    list_editable = ('available_seats', 'base_price')
    list_per_page = 20

    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'source_city', 'location', 'duration', 'category', 'description', 'image')
        }),
        ('Pricing & Capacity', {
            'fields': ('base_price', 'max_persons', 'min_persons', 'available_seats')
        }),
        ('Trip Details', {
            'fields': ('triptime',),
            'classes': ('wide',)
        }),
    )

    def booking_count(self, obj):
        count = Booking.objects.filter(package=obj).count()
        # Correct URL pattern for admin
        url = reverse('admin:Tours_booking_changelist') + f'?package__id={obj.id}'
        return format_html('<a href="{}" style="font-weight: bold;">{} Bookings</a>', url, count)

    booking_count.short_description = 'Total Bookings'

    def revenue_generated(self, obj):
        total = Booking.objects.filter(package=obj).aggregate(total=models.Sum('total_price'))['total'] or 0
        return format_html('<span style="color: #28a745; font-weight: bold;">₹{}</span>', total)

    revenue_generated.short_description = 'Revenue'

    def triptime_display(self, obj):
        if obj.triptime:
            return obj.triptime.strftime('%d %b %Y, %I:%M %p')
        return '-'

    triptime_display.short_description = 'Trip Time'
    triptime_display.admin_order_field = 'triptime'


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'customer_info',
        'package_info',
        'payment_status_check',
        'booking_status_colored',
        'persons',
        'travel_mode_icon',
        'package_type_badge',
        'total_price_colored',
        'booking_date_display',
        'travel_date_display',
        'actions_dropdown',
    )
    list_display_links = ('id', 'customer_info')
    list_filter = (
        'booking_status',
        'package_type',
        'travel_mode',
        'booking_date',
        'package__category',
    )
    search_fields = (
        'user__name',
        'user__email',
        'package__title',
        'package__location',
        'message'
    )
    list_per_page = 25
    date_hierarchy = 'booking_date'

    fieldsets = (
        ('Customer Information', {
            'fields': ('user',)
        }),
        ('Package Details', {
            'fields': ('package', 'persons', 'travel_mode', 'package_type')
        }),
        ('Dates', {
            'fields': ('travel_date', 'booking_date'),
            'classes': ('wide',)
        }),
        ('Payment Verification', {  # Updated Section
            'fields': ('total_price', 'payment_screenshot', 'payment_preview', 'booking_status', 'message'),
            'classes': ('wide',)
        }),
    )

    readonly_fields = ('booking_date','payment_preview')
    actions = ['mark_as_confirmed', 'mark_as_cancelled', 'mark_as_pending', 'send_reminder']

    def payment_status_check(self, obj):
        if obj.payment_screenshot:
            return format_html(
                '<a href="{}" target="_blank">'
                '<img src="{}" style="width: 45px; height: 45px; border-radius: 5px; object-fit: cover; border: 1px solid #ddd;"/>'
                '</a>',
                obj.payment_screenshot.url, obj.payment_screenshot.url
            )
        return format_html('<span style="color: #999;">No Screenshot</span>')

    payment_status_check.short_description = 'Payment'

    # 2. Method for the Large Preview in the Edit Form
    def payment_preview(self, obj):
        if obj.payment_screenshot:
            return format_html(
                '<div style="margin-bottom: 10px;">'
                '<a href="{}" target="_blank">'
                '<img src="{}" style="max-width: 300px; border: 2px solid #ccc; border-radius: 10px;"/>'
                '</a>'
                '<p><small>Click image to view full size</small></p></div>',
                obj.payment_screenshot.url, obj.payment_screenshot.url
            )
        return "No payment screenshot uploaded yet."

    payment_preview.short_description = "Screenshot Preview"
    def customer_info(self, obj):
        # Correct URL pattern for user change
        url = reverse('admin:Tours_userregistration_change', args=[obj.user.id])
        return format_html(
            '<a href="{}" style="font-weight: bold;">{}</a><br>'
            '<small style="color: #666;">{}</small>',
            url, obj.user.name, obj.user.email
        )

    customer_info.short_description = 'Customer'

    def package_info(self, obj):
        # Correct URL pattern for package change
        url = reverse('admin:Tours_package_change', args=[obj.package.id])
        return format_html(
            '<a href="{}" style="font-weight: bold;">{}</a><br>'
            '<small style="color: #666;">{}</small>',
            url, obj.package.title, obj.package.location
        )

    package_info.short_description = 'Package'

    # def booking_status_colored(self, obj):
    #     colors = {
    #         'confirmed': '#28a745',
    #         'pending': '#ffc107',
    #         'cancelled': '#dc3545'
    #     }
    #     icons = {
    #         'confirmed': '✓',
    #         'pending': '⏳',
    #         'cancelled': '✗'
    #     }
    #     return format_html(
    #         '<span style="background-color: {}; color: {}; padding: 3px 10px; '
    #         'border-radius: 12px; font-size: 12px; font-weight: bold;">'
    #         '{} {}</span>',
    #         colors.get(obj.booking_status, '#6c757d'),
    #         'black' if obj.booking_status == 'pending' else 'white',
    #         icons.get(obj.booking_status, ''),
    #         obj.get_booking_status_display()
    #     )
    #
    # booking_status_colored.short_description = 'Status'
    # admin.py inside BookingAdmin class

    # In your BookingAdmin class, update the booking_status_colored method

    def booking_status_colored(self, obj):
        colors = {
            'confirmed': '#28a745',
            'pending': '#ffc107',
            'cancelled': '#dc3545',
            'waiting': '#17a2b8'  # Teal for Waiting List
        }
        icons = {
            'confirmed': '✓',
            'pending': '⏳',
            'cancelled': '✗',
            'waiting': '🕒'  # Clock icon for waiting list
        }

        status_display = obj.get_booking_status_display()

        # Show waiting list position
        if obj.booking_status == 'waiting':
            position = obj.get_waiting_list_position()
            if position:
                status_display = f"Waiting (WL{position})"
            elif obj.message:
                status_display = f"Waiting ({obj.message})"

        return format_html(
            '<span style="background-color: {}; color: {}; padding: 3px 10px; '
            'border-radius: 12px; font-size: 12px; font-weight: bold;">'
            '{} {}</span>',
            colors.get(obj.booking_status, '#6c757d'),
            'black' if obj.booking_status == 'pending' else 'white',
            icons.get(obj.booking_status, ''),
            status_display
        )

    booking_status_colored.short_description = 'Status'

    # Add custom admin action for promoting from waiting list
    def promote_from_waiting_list(self, request, queryset):
        for booking in queryset.filter(booking_status='waiting'):
            if booking.package.available_seats >= booking.persons:
                # Promote this booking
                booking.booking_status = 'pending'
                booking.promoted_from_waiting = True
                booking.message = "Promoted from Waiting List"
                booking.save()

                # Reduce available seats
                booking.package.available_seats -= booking.persons
                booking.package.save()

                # Update remaining waiting list positions
                booking.update_waiting_list_positions()

                self.message_user(request, f"Booking #{booking.id} promoted from waiting list.")
            else:
                self.message_user(request, f"Not enough seats to promote Booking #{booking.id}", level='WARNING')

    promote_from_waiting_list.short_description = "Promote selected from waiting list"
    def travel_mode_icon(self, obj):
        icons = {
            'bus': '🚌',
            'train': '🚂',
            'flight': '✈️',
            'car': '🚗',
            'bike': '🏍️'
        }
        return format_html(
            '{} <span style="color: #666;">{}</span>',
            icons.get(obj.travel_mode, '🚍'),
            obj.get_travel_mode_display()
        )

    travel_mode_icon.short_description = 'Travel Mode'

    def package_type_badge(self, obj):
        colors = {
            'standard': '#6c757d',
            'premium': '#ffc107',
            'vip': '#dc3545'
        }
        return format_html(
            '<span style="background-color: {}; color: {}; padding: 3px 8px; '
            'border-radius: 12px; font-size: 11px; font-weight: bold;">{}</span>',
            colors.get(obj.package_type, '#6c757d'),
            'black' if obj.package_type == 'premium' else 'white',
            obj.get_package_type_display().upper()
        )

    package_type_badge.short_description = 'Package Type'

    def total_price_colored(self, obj):
        return format_html(
            '<span style="color: #28a745; font-weight: bold; font-size: 16px;">'
            '₹{}</span>',
            obj.total_price
        )

    total_price_colored.short_description = 'Total Price'

    def booking_date_display(self, obj):
        return obj.booking_date.strftime('%d %b %Y<br>%I:%M %p')

    booking_date_display.short_description = 'Booking Date'
    booking_date_display.admin_order_field = 'booking_date'

    def travel_date_display(self, obj):
        try:
            from datetime import datetime
            date_obj = datetime.strptime(obj.travel_date, '%Y-%m-%dT%H:%M')
            return date_obj.strftime('%d %b %Y, %I:%M %p')
        except:
            return obj.travel_date

    travel_date_display.short_description = 'Travel Date'

    def actions_dropdown(self, obj):
        if obj.booking_status == 'cancelled':
            return format_html('<span style="color: #dc3545;">❌ Cancelled</span>')

        buttons = []
        if obj.booking_status != 'confirmed':
            buttons.append(
                f'<a href="/admin/Tours/booking/{obj.id}/confirm/" '
                f'style="background: #28a745; color: white; padding: 3px 8px; '
                f'border-radius: 3px; text-decoration: none; margin-right: 5px; '
                f'onclick="return confirm(\'Confirm this booking?\');">✓ Confirm</a>'
            )
        if obj.booking_status != 'cancelled':
            buttons.append(
                f'<a href="/admin/Tours/booking/{obj.id}/cancel/" '
                f'style="background: #dc3545; color: white; padding: 3px 8px; '
                f'border-radius: 3px; text-decoration: none; '
                f'onclick="return confirm(\'Are you sure you want to CANCEL this booking?\\n\\nNote: Available seats will be increased!\');">✗ Cancel</a>'
            )

        return format_html(' '.join(buttons))

    actions_dropdown.short_description = 'Actions'

    # Custom Actions
    def mark_as_confirmed(self, request, queryset):
        for booking in queryset:
            if booking.booking_status != 'confirmed':
                booking.booking_status = 'confirmed'
                booking.save()
        self.message_user(request, f"{queryset.count()} bookings marked as confirmed.")

    mark_as_confirmed.short_description = "Mark selected as Confirmed"

    def mark_as_cancelled(self, request, queryset):
        for booking in queryset:
            if booking.booking_status != 'cancelled':
                # Increase available seats when cancelled
                booking.package.available_seats += booking.persons
                booking.package.save()
                booking.booking_status = 'cancelled'
                booking.save()
        self.message_user(request, f"{queryset.count()} bookings cancelled and seats released.")

    mark_as_cancelled.short_description = "Cancel selected bookings"

    def mark_as_pending(self, request, queryset):
        queryset.update(booking_status='pending')
        self.message_user(request, f"{queryset.count()} bookings marked as pending.")

    mark_as_pending.short_description = "Mark selected as Pending"

    def send_reminder(self, request, queryset):
        # You can implement email/SMS reminder here
        self.message_user(request, f"Reminders sent for {queryset.count()} bookings.")

    send_reminder.short_description = "Send reminder to selected"

    # Override delete to handle seat availability
    def delete_queryset(self, request, queryset):
        for booking in queryset:
            if booking.booking_status != 'cancelled':
                booking.package.available_seats += booking.persons
                booking.package.save()
        super().delete_queryset(request, queryset)


# Add this to your admin.py

@admin.register(PassengerDetail)
class PassengerDetailAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'age', 'gender', 'booking_link', 'aadhar_number', 'created_at')
    list_filter = ('gender', 'created_at')
    search_fields = ('name', 'aadhar_number', 'booking__id')
    list_per_page = 25

    def booking_link(self, obj):
        url = reverse('admin:Tours_booking_change', args=[obj.booking.id])
        return format_html('<a href="{}">Booking #{}</a>', url, obj.booking.id)

    booking_link.short_description = 'Booking'


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    # What columns to show in the list view
    list_display = ('user_name', 'rating_stars', 'message_snippet', 'is_approved', 'created_at')

    # Filters on the right side
    list_filter = ('is_approved', 'rating', 'created_at')

    # Search box functionality
    search_fields = ('user__name', 'message')

    # Allows you to click the checkmark directly in the list
    list_editable = ('is_approved',)

    # Custom actions at the top
    actions = ['approve_feedback']

    def user_name(self, obj):
        return obj.user.name

    user_name.short_description = 'Customer Name'

    def rating_stars(self, obj):
        # Displays actual gold stars in the admin panel
        stars = '⭐' * obj.rating
        return format_html('<span style="color: #ffc107;">{}</span>', stars)

    rating_stars.short_description = 'Rating'

    def message_snippet(self, obj):
        # Shows only the first 50 characters of the review
        return obj.message[:50] + "..." if len(obj.message) > 50 else obj.message

    message_snippet.short_description = 'Review Text'

    def approve_feedback(self, request, queryset):
        queryset.update(is_approved=True)

    approve_feedback.short_description = "✅ Approve selected reviews"




@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'subject', 'created_at', 'is_read')
    list_filter = ('is_read', 'created_at')
    search_fields = ('name', 'email', 'subject', 'message')
    readonly_fields = ('name', 'email', 'subject', 'message', 'created_at')
    list_editable = ('is_read',)

    fieldsets = (
        ('Contact Information', {
            'fields': ('name', 'email', 'subject', 'message')
        }),
        ('Status', {
            'fields': ('is_read', 'created_at')
        }),
    )

    actions = ['mark_as_read', 'mark_as_unread']

    def mark_as_read(self, request, queryset):
        queryset.update(is_read=True)

    mark_as_read.short_description = "Mark selected messages as read"

    def mark_as_unread(self, request, queryset):
        queryset.update(is_read=False)

    mark_as_unread.short_description = "Mark selected messages as unread"