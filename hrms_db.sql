-- ==========================================================================
-- Company Enterprise HRMS - Complete MySQL Database Export
-- Compatible with MySQL 8.0+, 5.7+, MariaDB, phpMyAdmin & MySQL Workbench
-- ==========================================================================

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;
SET SQL_MODE = 'NO_AUTO_VALUE_ON_ZERO';
SET time_zone = '+05:30';

CREATE DATABASE IF NOT EXISTS `hrms_db` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `hrms_db`;

DROP TABLE IF EXISTS `django_migrations`;
CREATE TABLE `django_migrations` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `app` VARCHAR(255) NOT NULL,
  `name` VARCHAR(255) NOT NULL,
  `applied` DATETIME(6) NULL NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Dumping data for table `django_migrations` (30 records)
INSERT INTO `django_migrations` (`id`, `app`, `name`, `applied`) VALUES
  (1, 'contenttypes', '0001_initial', '2026-11-01 15:05:40.132503'),
  (2, 'contenttypes', '0002_remove_content_type_name', '2026-11-01 15:05:40.141117'),
  (3, 'auth', '0001_initial', '2026-11-01 15:05:40.158578'),
  (4, 'auth', '0002_alter_permission_name_max_length', '2026-11-01 15:05:40.166566'),
  (5, 'auth', '0003_alter_user_email_max_length', '2026-11-01 15:05:40.171289'),
  (6, 'auth', '0004_alter_user_username_opts', '2026-11-01 15:05:40.176841'),
  (7, 'auth', '0005_alter_user_last_login_null', '2026-11-01 15:05:40.181898'),
  (8, 'auth', '0006_require_contenttypes_0002', '2026-11-01 15:05:40.185112'),
  (9, 'auth', '0007_alter_validators_add_error_messages', '2026-11-01 15:05:40.190183'),
  (10, 'auth', '0008_alter_user_username_max_length', '2026-11-01 15:05:40.195948'),
  (11, 'auth', '0009_alter_user_last_name_max_length', '2026-11-01 15:05:40.201340'),
  (12, 'auth', '0010_alter_group_name_max_length', '2026-11-01 15:05:40.208344'),
  (13, 'auth', '0011_update_proxy_permissions', '2026-11-01 15:05:40.213006'),
  (14, 'auth', '0012_alter_user_first_name_max_length', '2026-11-01 15:05:40.218759'),
  (15, 'accounts', '0001_initial', '2026-11-01 15:05:40.236035'),
  (16, 'admin', '0001_initial', '2026-11-01 15:05:40.247476'),
  (17, 'admin', '0002_logentry_remove_auto_add', '2026-11-01 15:05:40.258759'),
  (18, 'admin', '0003_logentry_add_action_flag_choices', '2026-11-01 15:05:40.265684'),
  (19, 'organization', '0001_initial', '2026-11-01 15:05:40.330492'),
  (20, 'employees', '0001_initial', '2026-11-01 15:05:40.370066'),
  (21, 'attendance', '0001_initial', '2026-11-01 15:05:40.412139'),
  (22, 'leave_management', '0001_initial', '2026-11-01 15:05:40.449859'),
  (23, 'notifications', '0001_initial', '2026-11-01 15:05:40.478619'),
  (24, 'payroll', '0001_initial', '2026-11-01 15:05:40.532761'),
  (25, 'performance', '0001_initial', '2026-11-01 15:05:40.595921'),
  (26, 'sessions', '0001_initial', '2026-11-01 15:05:40.605298'),
  (27, 'support', '0001_initial', '2026-11-01 15:05:40.700764'),
  (28, 'recruitment', '0001_initial', '2026-11-02 10:26:49.270794'),
  (29, 'recruitment', '0002_candidate_aadhaar_number_and_more', '2026-11-02 12:00:39.316600'),
  (30, 'recruitment', '0003_candidate_pf_uan_number', '2026-11-04 07:25:06.215838');


DROP TABLE IF EXISTS `django_content_type`;
CREATE TABLE `django_content_type` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `app_label` VARCHAR(100) NOT NULL,
  `model` VARCHAR(100) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Dumping data for table `django_content_type` (48 records)
INSERT INTO `django_content_type` (`id`, `app_label`, `model`) VALUES
  (1, 'admin', 'logentry'),
  (2, 'auth', 'permission'),
  (3, 'auth', 'group'),
  (4, 'contenttypes', 'contenttype'),
  (5, 'sessions', 'session'),
  (6, 'accounts', 'customuser'),
  (7, 'accounts', 'auditlog'),
  (8, 'organization', 'companypolicy'),
  (9, 'organization', 'holiday'),
  (10, 'organization', 'companyevent'),
  (11, 'organization', 'department'),
  (12, 'organization', 'eventgallery'),
  (13, 'organization', 'site'),
  (14, 'organization', 'announcement'),
  (15, 'organization', 'announcementread'),
  (16, 'organization', 'designation'),
  (17, 'organization', 'eventparticipant'),
  (18, 'organization', 'policyacknowledgement'),
  (19, 'employees', 'employeeprofile'),
  (20, 'employees', 'employeedocument'),
  (21, 'employees', 'profilecorrectionrequest'),
  (22, 'attendance', 'shift'),
  (23, 'attendance', 'attendance'),
  (24, 'attendance', 'attendanceauditlog'),
  (25, 'attendance', 'attendancecorrectionrequest'),
  (26, 'leave_management', 'leavetype'),
  (27, 'leave_management', 'leaverequest'),
  (28, 'leave_management', 'leavebalance'),
  (29, 'payroll', 'payrollperiod'),
  (30, 'payroll', 'salarystructure'),
  (31, 'payroll', 'payslip'),
  (32, 'performance', 'employeeaward'),
  (33, 'performance', 'goal'),
  (34, 'performance', 'performancereview'),
  (35, 'support', 'asset'),
  (36, 'support', 'officialdocumentrequest'),
  (37, 'support', 'supportticket'),
  (38, 'support', 'ticketcomment'),
  (39, 'notifications', 'notification'),
  (40, 'recruitment', 'candidate'),
  (41, 'recruitment', 'candidatedocument'),
  (42, 'recruitment', 'candidateeducation'),
  (43, 'recruitment', 'candidateexperience'),
  (44, 'recruitment', 'candidateregistrationlink'),
  (45, 'recruitment', 'candidateskill'),
  (46, 'recruitment', 'jobapplication'),
  (47, 'recruitment', 'applicationstatushistory'),
  (48, 'recruitment', 'recruitmentjob');


DROP TABLE IF EXISTS `auth_group_permissions`;
CREATE TABLE `auth_group_permissions` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `group_id` BIGINT NOT NULL,
  `permission_id` BIGINT NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS `auth_permission`;
CREATE TABLE `auth_permission` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `content_type_id` BIGINT NOT NULL,
  `codename` VARCHAR(100) NOT NULL,
  `name` VARCHAR(255) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Dumping data for table `auth_permission` (192 records)
INSERT INTO `auth_permission` (`id`, `content_type_id`, `codename`, `name`) VALUES
  (1, 1, 'add_logentry', 'Can add log entry'),
  (2, 1, 'change_logentry', 'Can change log entry'),
  (3, 1, 'delete_logentry', 'Can delete log entry'),
  (4, 1, 'view_logentry', 'Can view log entry'),
  (5, 2, 'add_permission', 'Can add permission'),
  (6, 2, 'change_permission', 'Can change permission'),
  (7, 2, 'delete_permission', 'Can delete permission'),
  (8, 2, 'view_permission', 'Can view permission'),
  (9, 3, 'add_group', 'Can add group'),
  (10, 3, 'change_group', 'Can change group'),
  (11, 3, 'delete_group', 'Can delete group'),
  (12, 3, 'view_group', 'Can view group'),
  (13, 4, 'add_contenttype', 'Can add content type'),
  (14, 4, 'change_contenttype', 'Can change content type'),
  (15, 4, 'delete_contenttype', 'Can delete content type'),
  (16, 4, 'view_contenttype', 'Can view content type'),
  (17, 5, 'add_session', 'Can add session'),
  (18, 5, 'change_session', 'Can change session'),
  (19, 5, 'delete_session', 'Can delete session'),
  (20, 5, 'view_session', 'Can view session'),
  (21, 6, 'add_customuser', 'Can add User'),
  (22, 6, 'change_customuser', 'Can change User'),
  (23, 6, 'delete_customuser', 'Can delete User'),
  (24, 6, 'view_customuser', 'Can view User'),
  (25, 7, 'add_auditlog', 'Can add audit log'),
  (26, 7, 'change_auditlog', 'Can change audit log'),
  (27, 7, 'delete_auditlog', 'Can delete audit log'),
  (28, 7, 'view_auditlog', 'Can view audit log'),
  (29, 8, 'add_companypolicy', 'Can add company policy'),
  (30, 8, 'change_companypolicy', 'Can change company policy'),
  (31, 8, 'delete_companypolicy', 'Can delete company policy'),
  (32, 8, 'view_companypolicy', 'Can view company policy'),
  (33, 9, 'add_holiday', 'Can add holiday'),
  (34, 9, 'change_holiday', 'Can change holiday'),
  (35, 9, 'delete_holiday', 'Can delete holiday'),
  (36, 9, 'view_holiday', 'Can view holiday'),
  (37, 10, 'add_companyevent', 'Can add company event'),
  (38, 10, 'change_companyevent', 'Can change company event'),
  (39, 10, 'delete_companyevent', 'Can delete company event'),
  (40, 10, 'view_companyevent', 'Can view company event'),
  (41, 11, 'add_department', 'Can add department'),
  (42, 11, 'change_department', 'Can change department'),
  (43, 11, 'delete_department', 'Can delete department'),
  (44, 11, 'view_department', 'Can view department'),
  (45, 12, 'add_eventgallery', 'Can add event gallery'),
  (46, 12, 'change_eventgallery', 'Can change event gallery'),
  (47, 12, 'delete_eventgallery', 'Can delete event gallery'),
  (48, 12, 'view_eventgallery', 'Can view event gallery'),
  (49, 13, 'add_site', 'Can add site'),
  (50, 13, 'change_site', 'Can change site');

INSERT INTO `auth_permission` (`id`, `content_type_id`, `codename`, `name`) VALUES
  (51, 13, 'delete_site', 'Can delete site'),
  (52, 13, 'view_site', 'Can view site'),
  (53, 14, 'add_announcement', 'Can add announcement'),
  (54, 14, 'change_announcement', 'Can change announcement'),
  (55, 14, 'delete_announcement', 'Can delete announcement'),
  (56, 14, 'view_announcement', 'Can view announcement'),
  (57, 15, 'add_announcementread', 'Can add announcement read'),
  (58, 15, 'change_announcementread', 'Can change announcement read'),
  (59, 15, 'delete_announcementread', 'Can delete announcement read'),
  (60, 15, 'view_announcementread', 'Can view announcement read'),
  (61, 16, 'add_designation', 'Can add designation'),
  (62, 16, 'change_designation', 'Can change designation'),
  (63, 16, 'delete_designation', 'Can delete designation'),
  (64, 16, 'view_designation', 'Can view designation'),
  (65, 17, 'add_eventparticipant', 'Can add event participant'),
  (66, 17, 'change_eventparticipant', 'Can change event participant'),
  (67, 17, 'delete_eventparticipant', 'Can delete event participant'),
  (68, 17, 'view_eventparticipant', 'Can view event participant'),
  (69, 18, 'add_policyacknowledgement', 'Can add policy acknowledgement'),
  (70, 18, 'change_policyacknowledgement', 'Can change policy acknowledgement'),
  (71, 18, 'delete_policyacknowledgement', 'Can delete policy acknowledgement'),
  (72, 18, 'view_policyacknowledgement', 'Can view policy acknowledgement'),
  (73, 19, 'add_employeeprofile', 'Can add employee profile'),
  (74, 19, 'change_employeeprofile', 'Can change employee profile'),
  (75, 19, 'delete_employeeprofile', 'Can delete employee profile'),
  (76, 19, 'view_employeeprofile', 'Can view employee profile'),
  (77, 20, 'add_employeedocument', 'Can add employee document'),
  (78, 20, 'change_employeedocument', 'Can change employee document'),
  (79, 20, 'delete_employeedocument', 'Can delete employee document'),
  (80, 20, 'view_employeedocument', 'Can view employee document'),
  (81, 21, 'add_profilecorrectionrequest', 'Can add profile correction request'),
  (82, 21, 'change_profilecorrectionrequest', 'Can change profile correction request'),
  (83, 21, 'delete_profilecorrectionrequest', 'Can delete profile correction request'),
  (84, 21, 'view_profilecorrectionrequest', 'Can view profile correction request'),
  (85, 22, 'add_shift', 'Can add shift'),
  (86, 22, 'change_shift', 'Can change shift'),
  (87, 22, 'delete_shift', 'Can delete shift'),
  (88, 22, 'view_shift', 'Can view shift'),
  (89, 23, 'add_attendance', 'Can add attendance'),
  (90, 23, 'change_attendance', 'Can change attendance'),
  (91, 23, 'delete_attendance', 'Can delete attendance'),
  (92, 23, 'view_attendance', 'Can view attendance'),
  (93, 24, 'add_attendanceauditlog', 'Can add attendance audit log'),
  (94, 24, 'change_attendanceauditlog', 'Can change attendance audit log'),
  (95, 24, 'delete_attendanceauditlog', 'Can delete attendance audit log'),
  (96, 24, 'view_attendanceauditlog', 'Can view attendance audit log'),
  (97, 25, 'add_attendancecorrectionrequest', 'Can add attendance correction request'),
  (98, 25, 'change_attendancecorrectionrequest', 'Can change attendance correction request'),
  (99, 25, 'delete_attendancecorrectionrequest', 'Can delete attendance correction request'),
  (100, 25, 'view_attendancecorrectionrequest', 'Can view attendance correction request');

INSERT INTO `auth_permission` (`id`, `content_type_id`, `codename`, `name`) VALUES
  (101, 26, 'add_leavetype', 'Can add leave type'),
  (102, 26, 'change_leavetype', 'Can change leave type'),
  (103, 26, 'delete_leavetype', 'Can delete leave type'),
  (104, 26, 'view_leavetype', 'Can view leave type'),
  (105, 27, 'add_leaverequest', 'Can add leave request'),
  (106, 27, 'change_leaverequest', 'Can change leave request'),
  (107, 27, 'delete_leaverequest', 'Can delete leave request'),
  (108, 27, 'view_leaverequest', 'Can view leave request'),
  (109, 28, 'add_leavebalance', 'Can add leave balance'),
  (110, 28, 'change_leavebalance', 'Can change leave balance'),
  (111, 28, 'delete_leavebalance', 'Can delete leave balance'),
  (112, 28, 'view_leavebalance', 'Can view leave balance'),
  (113, 29, 'add_payrollperiod', 'Can add payroll period'),
  (114, 29, 'change_payrollperiod', 'Can change payroll period'),
  (115, 29, 'delete_payrollperiod', 'Can delete payroll period'),
  (116, 29, 'view_payrollperiod', 'Can view payroll period'),
  (117, 30, 'add_salarystructure', 'Can add salary structure'),
  (118, 30, 'change_salarystructure', 'Can change salary structure'),
  (119, 30, 'delete_salarystructure', 'Can delete salary structure'),
  (120, 30, 'view_salarystructure', 'Can view salary structure'),
  (121, 31, 'add_payslip', 'Can add payslip'),
  (122, 31, 'change_payslip', 'Can change payslip'),
  (123, 31, 'delete_payslip', 'Can delete payslip'),
  (124, 31, 'view_payslip', 'Can view payslip'),
  (125, 32, 'add_employeeaward', 'Can add employee award'),
  (126, 32, 'change_employeeaward', 'Can change employee award'),
  (127, 32, 'delete_employeeaward', 'Can delete employee award'),
  (128, 32, 'view_employeeaward', 'Can view employee award'),
  (129, 33, 'add_goal', 'Can add goal'),
  (130, 33, 'change_goal', 'Can change goal'),
  (131, 33, 'delete_goal', 'Can delete goal'),
  (132, 33, 'view_goal', 'Can view goal'),
  (133, 34, 'add_performancereview', 'Can add performance review'),
  (134, 34, 'change_performancereview', 'Can change performance review'),
  (135, 34, 'delete_performancereview', 'Can delete performance review'),
  (136, 34, 'view_performancereview', 'Can view performance review'),
  (137, 35, 'add_asset', 'Can add asset'),
  (138, 35, 'change_asset', 'Can change asset'),
  (139, 35, 'delete_asset', 'Can delete asset'),
  (140, 35, 'view_asset', 'Can view asset'),
  (141, 36, 'add_officialdocumentrequest', 'Can add official document request'),
  (142, 36, 'change_officialdocumentrequest', 'Can change official document request'),
  (143, 36, 'delete_officialdocumentrequest', 'Can delete official document request'),
  (144, 36, 'view_officialdocumentrequest', 'Can view official document request'),
  (145, 37, 'add_supportticket', 'Can add support ticket'),
  (146, 37, 'change_supportticket', 'Can change support ticket'),
  (147, 37, 'delete_supportticket', 'Can delete support ticket'),
  (148, 37, 'view_supportticket', 'Can view support ticket'),
  (149, 38, 'add_ticketcomment', 'Can add ticket comment'),
  (150, 38, 'change_ticketcomment', 'Can change ticket comment');

INSERT INTO `auth_permission` (`id`, `content_type_id`, `codename`, `name`) VALUES
  (151, 38, 'delete_ticketcomment', 'Can delete ticket comment'),
  (152, 38, 'view_ticketcomment', 'Can view ticket comment'),
  (153, 39, 'add_notification', 'Can add notification'),
  (154, 39, 'change_notification', 'Can change notification'),
  (155, 39, 'delete_notification', 'Can delete notification'),
  (156, 39, 'view_notification', 'Can view notification'),
  (157, 40, 'add_candidate', 'Can add candidate'),
  (158, 40, 'change_candidate', 'Can change candidate'),
  (159, 40, 'delete_candidate', 'Can delete candidate'),
  (160, 40, 'view_candidate', 'Can view candidate'),
  (161, 41, 'add_candidatedocument', 'Can add candidate document'),
  (162, 41, 'change_candidatedocument', 'Can change candidate document'),
  (163, 41, 'delete_candidatedocument', 'Can delete candidate document'),
  (164, 41, 'view_candidatedocument', 'Can view candidate document'),
  (165, 42, 'add_candidateeducation', 'Can add candidate education'),
  (166, 42, 'change_candidateeducation', 'Can change candidate education'),
  (167, 42, 'delete_candidateeducation', 'Can delete candidate education'),
  (168, 42, 'view_candidateeducation', 'Can view candidate education'),
  (169, 43, 'add_candidateexperience', 'Can add candidate experience'),
  (170, 43, 'change_candidateexperience', 'Can change candidate experience'),
  (171, 43, 'delete_candidateexperience', 'Can delete candidate experience'),
  (172, 43, 'view_candidateexperience', 'Can view candidate experience'),
  (173, 44, 'add_candidateregistrationlink', 'Can add candidate registration link'),
  (174, 44, 'change_candidateregistrationlink', 'Can change candidate registration link'),
  (175, 44, 'delete_candidateregistrationlink', 'Can delete candidate registration link'),
  (176, 44, 'view_candidateregistrationlink', 'Can view candidate registration link'),
  (177, 45, 'add_candidateskill', 'Can add candidate skill'),
  (178, 45, 'change_candidateskill', 'Can change candidate skill'),
  (179, 45, 'delete_candidateskill', 'Can delete candidate skill'),
  (180, 45, 'view_candidateskill', 'Can view candidate skill'),
  (181, 46, 'add_jobapplication', 'Can add job application'),
  (182, 46, 'change_jobapplication', 'Can change job application'),
  (183, 46, 'delete_jobapplication', 'Can delete job application'),
  (184, 46, 'view_jobapplication', 'Can view job application'),
  (185, 47, 'add_applicationstatushistory', 'Can add application status history'),
  (186, 47, 'change_applicationstatushistory', 'Can change application status history'),
  (187, 47, 'delete_applicationstatushistory', 'Can delete application status history'),
  (188, 47, 'view_applicationstatushistory', 'Can view application status history'),
  (189, 48, 'add_recruitmentjob', 'Can add recruitment job'),
  (190, 48, 'change_recruitmentjob', 'Can change recruitment job'),
  (191, 48, 'delete_recruitmentjob', 'Can delete recruitment job'),
  (192, 48, 'view_recruitmentjob', 'Can view recruitment job');


DROP TABLE IF EXISTS `auth_group`;
CREATE TABLE `auth_group` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(150) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS `accounts_customuser`;
CREATE TABLE `accounts_customuser` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `password` VARCHAR(128) NOT NULL,
  `last_login` DATETIME(6) NULL,
  `is_superuser` TINYINT(1) NOT NULL,
  `username` VARCHAR(150) NOT NULL,
  `first_name` VARCHAR(150) NOT NULL,
  `last_name` VARCHAR(150) NOT NULL,
  `email` VARCHAR(254) NOT NULL,
  `is_staff` TINYINT(1) NOT NULL,
  `is_active` TINYINT(1) NOT NULL,
  `date_joined` DATETIME(6) NULL NOT NULL,
  `role` VARCHAR(20) NOT NULL,
  `phone` VARCHAR(20),
  `avatar` VARCHAR(100),
  `is_verified` TINYINT(1) NOT NULL,
  `theme_preference` VARCHAR(10) NOT NULL,
  `created_at` DATETIME(6) NULL NOT NULL,
  `updated_at` DATETIME(6) NULL NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Dumping data for table `accounts_customuser` (9 records)
INSERT INTO `accounts_customuser` (`id`, `password`, `last_login`, `is_superuser`, `username`, `first_name`, `last_name`, `email`, `is_staff`, `is_active`, `date_joined`, `role`, `phone`, `avatar`, `is_verified`, `theme_preference`, `created_at`, `updated_at`) VALUES
  (1, 'pbkdf2_sha256$870000$VyQIa8fxeeJ6C7wk3mlKAu$G9O0bTBrSwXjQlSg5r+H9K8Ke+7wBpqFi4O9t2Xqc+A=', '2026-11-04 07:19:56.352278', 1, 'admin', 'Debasish', 'Mohapatra', 'head.admin@company.com', 1, 1, '2026-11-01 15:07:10.223077', 'head', '+91 98610 11223', '', 1, 'light', '2026-11-01 15:07:10.223311', '2026-11-05 09:08:53.209302'),
  (2, 'pbkdf2_sha256$870000$lUM6l4Mz5gRUI0bKExo6NJ$Q7BFvCWW0qh75EfHXGXBgD7JIhYOu0bklYlnC/2V/WQ=', '2026-11-05 09:10:49.759264', 0, 'hr_admin', 'Smruti Rekha', 'Swain', 'smruti.swain@company.com', 1, 1, '2026-11-01 15:07:10.650224', 'hr', '+91 94370 44556', 'avatars/sustain3.png', 1, 'light', '2026-11-01 15:07:10.650359', '2026-11-05 09:08:53.751652'),
  (3, 'pbkdf2_sha256$870000$9Ip8USkvPAzDKJeu4D36n2$Zo6GiT23Z6+Oik1fJ58wu0iUWc4WBtxP78VAxyortmg=', '2026-11-04 07:19:49.858244', 0, 'site_manager', 'Rajesh Kumar', 'Jena', 'rajesh.jena@company.com', 0, 1, '2026-11-01 15:07:11.061536', 'site_manager', '+91 97780 67890', '', 1, 'light', '2026-11-01 15:07:11.061697', '2026-11-05 09:08:54.281635'),
  (4, 'pbkdf2_sha256$870000$3pZdFitqzGVlBFGgC0oI1Z$Wz2wXvHmYkJI4CIXE/jLV00SLiIx0DkzO/vJB/9GFeA=', '2026-11-04 07:29:23.717291', 0, 'john_doe', 'Soumya Ranjan', 'Sahoo', 'soumya.sahoo@company.com', 0, 1, '2026-11-01 15:07:11.538620', 'employee', '+91 99370 23456', 'avatars/WhatsApp_Image_2025-06-16_at_10.32.58_7c2c3011.jpg', 1, 'light', '2026-11-01 15:07:11.538840', '2026-11-05 09:08:54.792884'),
  (5, 'pbkdf2_sha256$870000$NxxQRGsZkdUCcqOKPiWQ79$M7DHr4oRp9qup8DfvNR9e361+K1b/+CwJQ4NWVK/jSM=', NULL, 0, 'sarah_connor', 'Ananya', 'Mishra', 'ananya.mishra@company.com', 0, 1, '2026-11-01 15:07:12.132664', 'employee', '+91 98530 88990', '', 1, 'light', '2026-11-01 15:07:12.133011', '2026-11-05 09:08:55.321310'),
  (6, 'pbkdf2_sha256$870000$7pmvzQnqolLosCN7rtp3d8$DjsV0OlrBKlwpdVzP/6AbyFLMq8HhcUx1jAPQX44wWY=', NULL, 0, 'priya_patel', 'Swagatika', 'Behera', 'swagatika.behera@company.com', 0, 1, '2026-11-01 15:07:12.831006', 'employee', '+91 96920 56789', '', 1, 'light', '2026-11-01 15:07:12.831233', '2026-11-05 09:08:55.807538'),
  (7, 'pbkdf2_sha256$870000$ENwj82mUMF3W0n03uModfr$AjJd94ftSP0YMYS7QDsnUAf9glBBfxu7AMZPQOYDvoM=', NULL, 0, 'david_miller', 'Biswajit', 'Rout', 'biswajit.rout@company.com', 0, 1, '2026-11-01 15:07:13.503129', 'employee', '+91 94380 55667', '', 1, 'light', '2026-11-01 15:07:13.503330', '2026-11-05 09:08:56.269788'),
  (8, 'pbkdf2_sha256$870000$2c5mFQDlvZxxajYAuEQAR5$rlfWIzjXCG6d3wDcRjikLcrpnMlOYg1okzCl82BkpSo=', NULL, 0, 'slipu061', 'alex', 'kumar', 'slipu061@gmail.com', 0, 1, '2026-11-02 12:30:57.337390', 'employee', '+913456787898', '', 1, 'light', '2026-11-02 12:30:58.445119', '2026-11-02 12:30:58.445136'),
  (9, 'pbkdf2_sha256$870000$snir43h39c9KohbN8d3sZU$nkd1ZXKF0wlC6k+koH1RLBH/Zd3dQfquJMdNKYxE1NI=', '2026-11-04 11:16:28.315387', 0, 'rajani@123', 'rajani', 'kumar', 'rajani@gmail.com', 0, 1, '2026-11-04 09:50:36.506771', 'employee', '8765342345', '', 1, 'light', '2026-11-04 09:50:37.205577', '2026-11-04 09:55:34.433805');


DROP TABLE IF EXISTS `accounts_customuser_groups`;
CREATE TABLE `accounts_customuser_groups` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `customuser_id` BIGINT NOT NULL,
  `group_id` BIGINT NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS `accounts_customuser_user_permissions`;
CREATE TABLE `accounts_customuser_user_permissions` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `customuser_id` BIGINT NOT NULL,
  `permission_id` BIGINT NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS `accounts_auditlog`;
CREATE TABLE `accounts_auditlog` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `action` VARCHAR(50) NOT NULL,
  `module` VARCHAR(50) NOT NULL,
  `description` LONGTEXT NOT NULL,
  `ip_address` LONGTEXT,
  `created_at` DATETIME(6) NULL NOT NULL,
  `user_id` BIGINT,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Dumping data for table `accounts_auditlog` (112 records)
INSERT INTO `accounts_auditlog` (`id`, `action`, `module`, `description`, `ip_address`, `created_at`, `user_id`) VALUES
  (1, 'PAYROLL', 'Payroll Management', 'October 2026 monthly company-wide payroll processed by HR Admin Pooja Menon.', '192.168.1.10', '2026-11-01 15:07:14.909547', 2),
  (2, 'APPROVAL', 'Executive Approvals', 'October 2026 monthly payroll approved by Head of Company Vikramaditya Singhania.', '192.168.1.2', '2026-11-01 15:07:14.917037', 1),
  (3, 'LOGIN', 'Authentication', 'User john_doe logged in successfully.', NULL, '2026-11-01 15:32:21.165458', 4),
  (4, 'UPDATE', 'Attendance', 'Punch-out recorded for EMP101. Total hours: 8.07', '127.0.0.1', '2026-11-01 17:06:19.593207', 4),
  (5, 'LOGIN', 'Demo Switcher', 'Switched active user to hr_admin (hr).', NULL, '2026-11-01 17:09:45.802447', 2),
  (6, 'LOGIN', 'Demo Switcher', 'Switched active user to site_manager (site_manager).', NULL, '2026-11-01 18:57:58.459157', 3),
  (7, 'CREATE', 'Attendance', 'Punch-in recorded for EMP003 at 18:58:13', '127.0.0.1', '2026-11-01 18:58:13.701448', 3),
  (8, 'LOGIN', 'Demo Switcher', 'Switched active user to admin (head).', NULL, '2026-11-01 18:59:29.966555', 1),
  (9, 'LOGOUT', 'Authentication', 'User admin logged out.', NULL, '2026-11-02 09:55:26.707980', 1),
  (10, 'LOGIN', 'Authentication', 'User hr_admin logged in successfully.', NULL, '2026-11-02 09:55:53.715000', 2),
  (11, 'LOGIN', 'Demo Switcher', 'Switched active user to john_doe (employee).', NULL, '2026-11-02 10:09:06.443776', 4),
  (12, 'CREATE', 'Attendance', 'Punch-in recorded for EMP101 at 10:26:47', '127.0.0.1', '2026-11-02 10:26:47.490764', 4),
  (13, 'UPDATE', 'Attendance', 'Punch-out recorded for EMP101. Total hours: 0.0', '127.0.0.1', '2026-11-02 10:26:49.754157', 4),
  (14, 'LOGIN', 'Demo Switcher', 'Switched active user to hr_admin (hr).', NULL, '2026-11-02 11:37:17.328277', 2),
  (15, 'CREATE', 'Recruitment Links', 'Generated recruitment link \'nbbb\' for Senior Full-Stack Django Developer [Token: 15AVn0thgXNvIbeDieD7lA]', NULL, '2026-11-02 11:39:23.840680', 2),
  (16, 'UPDATE', 'Recruitment', 'Updated application HRMS-2026-10369 (alex kumar) to status: SUBMITTED', NULL, '2026-11-02 12:07:19.177087', 2),
  (17, 'LOGIN', 'Demo Switcher', 'Switched active user to john_doe (employee).', NULL, '2026-11-02 12:09:11.205579', 4),
  (18, 'LOGIN', 'Demo Switcher', 'Switched active user to hr_admin (hr).', NULL, '2026-11-02 12:10:05.952453', 2),
  (19, 'APPROVAL', 'Leave Management', 'Leave approved for EMP101 by hr_admin', NULL, '2026-11-02 12:12:43.554209', 2),
  (20, 'LOGIN', 'Demo Switcher', 'Switched active user to admin (head).', NULL, '2026-11-02 12:21:11.699647', 1),
  (21, 'UPDATE', 'Recruitment', 'Updated application HRMS-2026-10369 (alex kumar) to status: SHORTLISTED', NULL, '2026-11-02 12:22:02.190035', 1),
  (22, 'LOGIN', 'Demo Switcher', 'Switched active user to john_doe (employee).', NULL, '2026-11-02 12:23:27.422839', 4),
  (23, 'LOGIN', 'Demo Switcher', 'Switched active user to hr_admin (hr).', NULL, '2026-11-02 12:23:58.542212', 2),
  (24, 'UPDATE', 'Recruitment', 'Updated application HRMS-2026-10369 (alex kumar) to status: HIRED', NULL, '2026-11-02 12:25:45.155398', 2),
  (25, 'LOGIN', 'Demo Switcher', 'Switched active user to john_doe (employee).', NULL, '2026-11-02 12:30:18.231110', 4),
  (26, 'LOGIN', 'Demo Switcher', 'Switched active user to hr_admin (hr).', NULL, '2026-11-02 12:30:40.579387', 2),
  (27, 'LOGIN', 'Demo Switcher', 'Switched active user to john_doe (employee).', NULL, '2026-11-02 12:34:34.199182', 4),
  (28, 'UPDATE', 'User Profile', 'User john_doe updated profile information.', NULL, '2026-11-02 12:34:58.778761', 4),
  (29, 'UPDATE', 'User Profile', 'User john_doe updated profile information.', NULL, '2026-11-02 12:35:01.297836', 4),
  (30, 'LOGOUT', 'Authentication', 'User john_doe logged out.', NULL, '2026-11-02 12:56:32.030807', 4),
  (31, 'LOGIN', 'Authentication', 'User hr_admin logged in successfully.', NULL, '2026-11-02 12:56:58.894438', 2),
  (32, 'UPDATE', 'Recruitment', 'Updated application HRMS-2026-10369 (alex kumar) to status: HIRED', NULL, '2026-11-02 12:58:28.430952', 2),
  (33, 'LOGIN', 'Demo Switcher', 'Switched active user to admin (head).', NULL, '2026-11-02 13:00:39.363862', 1),
  (34, 'UPDATE', 'Recruitment', 'Updated application HRMS-2026-10369 (alex kumar) to status: HIRED', NULL, '2026-11-02 13:02:46.548575', 1),
  (35, 'LOGIN', 'Demo Switcher', 'Switched active user to admin (head).', NULL, '2026-11-02 13:02:54.848376', 1),
  (36, 'LOGIN', 'Demo Switcher', 'Switched active user to site_manager (site_manager).', NULL, '2026-11-02 13:03:52.185319', 3),
  (37, 'LOGIN', 'Demo Switcher', 'Switched active user to hr_admin (hr).', NULL, '2026-11-02 13:04:23.340618', 2),
  (38, 'UPDATE', 'Recruitment', 'Updated application HRMS-2026-10369 (alex kumar) to status: HIRED', NULL, '2026-11-02 13:04:46.889746', 2),
  (39, 'LOGOUT', 'Authentication', 'User hr_admin logged out.', NULL, '2026-11-02 13:06:31.542522', 2),
  (40, 'LOGIN', 'Authentication', 'User hr_admin logged in successfully.', NULL, '2026-11-02 13:07:14.927352', 2),
  (41, 'LOGIN', 'Demo Switcher', 'Switched active user to hr_admin (hr).', NULL, '2026-11-02 13:07:14.964933', 2),
  (42, 'UPDATE', 'Recruitment', 'Updated application HRMS-2026-10369 (alex kumar) to status: ONBOARDING_COMPLETED', NULL, '2026-11-02 13:08:09.886590', 2),
  (43, 'LOGOUT', 'Authentication', 'User hr_admin logged out.', NULL, '2026-11-02 13:09:21.451531', 2),
  (44, 'LOGIN', 'Authentication', 'User hr_admin logged in successfully.', NULL, '2026-11-02 13:16:20.877878', 2),
  (45, 'LOGIN', 'Demo Switcher', 'Switched active user to hr_admin (hr).', NULL, '2026-11-02 13:17:52.961734', 2),
  (46, 'LOGIN', 'Demo Switcher', 'Switched active user to admin (head).', NULL, '2026-11-02 13:18:01.449099', 1),
  (47, 'UPDATE', 'Recruitment', 'Updated application HRMS-2026-10369 (alex kumar) to status: ONBOARDING_COMPLETED', NULL, '2026-11-02 13:18:18.832254', 1),
  (48, 'UPDATE', 'Recruitment', 'Updated application HRMS-2026-10369 (alex kumar) to status: HIRED', NULL, '2026-11-02 13:18:32.484496', 1),
  (49, 'UPDATE', 'Recruitment', 'Updated application HRMS-2026-10369 (alex kumar) to status: ONBOARDING_COMPLETED', NULL, '2026-11-02 13:18:49.296446', 1),
  (50, 'LOGIN', 'Authentication', 'User hr_admin logged in successfully.', NULL, '2026-11-02 13:33:56.908817', 2);

INSERT INTO `accounts_auditlog` (`id`, `action`, `module`, `description`, `ip_address`, `created_at`, `user_id`) VALUES
  (51, 'LOGIN', 'Authentication', 'User hr_admin logged in successfully.', NULL, '2026-11-02 15:58:28.792646', 2),
  (52, 'LOGIN', 'Authentication', 'User hr_admin logged in successfully.', NULL, '2026-11-03 04:16:33.979052', 2),
  (53, 'UPDATE', 'Recruitment', 'Updated application APP-46781 (Rohan Varma) to status: ON_HOLD', NULL, '2026-11-03 04:50:01.466547', 2),
  (54, 'LOGIN', 'Authentication', 'User hr_admin logged in successfully.', NULL, '2026-11-03 04:58:57.923652', 2),
  (55, 'LOGIN', 'Demo Switcher', 'Switched active user to admin (head).', NULL, '2026-11-03 05:46:45.678910', 1),
  (56, 'LOGIN', 'Demo Switcher', 'Switched active user to hr_admin (hr).', NULL, '2026-11-03 05:49:46.789662', 2),
  (57, 'LOGIN', 'Demo Switcher', 'Switched active user to site_manager (site_manager).', NULL, '2026-11-03 05:59:12.652452', 3),
  (58, 'LOGIN', 'Demo Switcher', 'Switched active user to hr_admin (hr).', NULL, '2026-11-03 06:03:31.555998', 2),
  (59, 'LOGIN', 'Demo Switcher', 'Switched active user to admin (head).', NULL, '2026-11-03 06:06:41.405642', 1),
  (60, 'LOGIN', 'Demo Switcher', 'Switched active user to hr_admin (hr).', NULL, '2026-11-03 06:07:59.457916', 2),
  (61, 'LOGIN', 'Demo Switcher', 'Switched active user to admin (head).', NULL, '2026-11-03 06:13:44.861652', 1),
  (62, 'CREATE', 'Attendance', 'Punch-in recorded for EMP001 at 06:14:03', '127.0.0.1', '2026-11-03 06:14:03.799218', 1),
  (63, 'LOGIN', 'Demo Switcher', 'Switched active user to hr_admin (hr).', NULL, '2026-11-03 06:21:52.081003', 2),
  (64, 'LOGIN', 'Demo Switcher', 'Switched active user to admin (head).', NULL, '2026-11-03 06:36:26.373477', 1),
  (65, 'LOGIN', 'Demo Switcher', 'Switched active user to hr_admin (hr).', NULL, '2026-11-03 06:37:16.484896', 2),
  (66, 'LOGIN', 'Demo Switcher', 'Switched active user to admin (head).', NULL, '2026-11-03 07:33:58.856411', 1),
  (67, 'LOGIN', 'Demo Switcher', 'Switched active user to hr_admin (hr).', NULL, '2026-11-03 07:35:24.295126', 2),
  (68, 'LOGIN', 'Demo Switcher', 'Switched active user to admin (head).', NULL, '2026-11-03 10:11:53.190946', 1),
  (69, 'LOGIN', 'Demo Switcher', 'Switched active user to hr_admin (hr).', NULL, '2026-11-03 10:13:00.549528', 2),
  (70, 'LOGIN', 'Authentication', 'User hr_admin logged in successfully.', NULL, '2026-11-04 04:31:12.759384', 2),
  (71, 'UPDATE', 'Recruitment', 'Updated application APP-78277 (arti sha) to status: REJECTED', NULL, '2026-11-04 06:04:37.745118', 2),
  (72, 'UPDATE', 'Recruitment', 'Updated application APP-78277 (arti sha) to status: HIRED', NULL, '2026-11-04 06:09:06.997556', 2),
  (73, 'UPDATE', 'Recruitment', 'Updated application APP-78277 (arti sha) to status: REJECTED', NULL, '2026-11-04 06:19:28.439003', 2),
  (74, 'UPDATE', 'Recruitment', 'Updated application APP-78277 (arti sha) to status: HIRED', NULL, '2026-11-04 06:20:03.639645', 2),
  (75, 'LOGIN', 'Demo Switcher', 'Switched active user to admin (head).', NULL, '2026-11-04 06:21:55.206332', 1),
  (76, 'LOGIN', 'Demo Switcher', 'Switched active user to hr_admin (hr).', NULL, '2026-11-04 06:22:25.338951', 2),
  (77, 'LOGIN', 'Demo Switcher', 'Switched active user to hr_admin (hr).', NULL, '2026-11-04 07:02:06.736545', 2),
  (78, 'LOGIN', 'Demo Switcher', 'Switched active user to site_manager (site_manager).', NULL, '2026-11-04 07:19:49.867199', 3),
  (79, 'LOGIN', 'Demo Switcher', 'Switched active user to admin (head).', NULL, '2026-11-04 07:19:56.358615', 1),
  (80, 'LOGIN', 'Demo Switcher', 'Switched active user to hr_admin (hr).', NULL, '2026-11-04 07:19:59.737778', 2),
  (81, 'LOGIN', 'Demo Switcher', 'Switched active user to john_doe (employee).', NULL, '2026-11-04 07:20:31.761594', 4),
  (82, 'LOGIN', 'Demo Switcher', 'Switched active user to hr_admin (hr).', NULL, '2026-11-04 07:23:59.508300', 2),
  (83, 'LOGIN', 'Demo Switcher', 'Switched active user to john_doe (employee).', NULL, '2026-11-04 07:29:23.724420', 4),
  (84, 'LOGIN', 'Demo Switcher', 'Switched active user to hr_admin (hr).', NULL, '2026-11-04 07:30:50.071430', 2),
  (85, 'LOGOUT', 'Authentication', 'User hr_admin logged out.', NULL, '2026-11-04 07:46:29.485852', 2),
  (86, 'LOGIN', 'Authentication', 'User hr_admin logged in successfully.', NULL, '2026-11-04 07:46:51.190637', 2),
  (87, 'LOGOUT', 'Authentication', 'User hr_admin logged out.', NULL, '2026-11-04 08:50:40.229475', 2),
  (88, 'LOGIN', 'Authentication', 'User hr_admin logged in successfully.', NULL, '2026-11-04 08:51:27.853615', 2),
  (89, 'LOGOUT', 'Authentication', 'User hr_admin logged out.', NULL, '2026-11-04 09:22:14.787152', 2),
  (90, 'LOGIN', 'Authentication', 'User hr_admin logged in successfully.', NULL, '2026-11-04 09:24:08.039663', 2),
  (91, 'LOGOUT', 'Authentication', 'User hr_admin logged out.', NULL, '2026-11-04 09:25:36.934528', 2),
  (92, 'LOGIN', 'Authentication', 'User hr_admin logged in successfully.', NULL, '2026-11-04 09:33:40.509072', 2),
  (93, 'CREATE', 'Employee Management', 'New employee created: EMP113 (rajani kumar)', NULL, '2026-11-04 09:50:37.245653', 2),
  (94, 'LOGIN', 'Authentication', 'User rajani@123 logged in successfully.', NULL, '2026-11-04 09:52:35.751651', 9),
  (95, 'CREATE', 'Attendance', 'Punch-in recorded for EMP113 at 09:52:51', '127.0.0.1', '2026-11-04 09:52:51.267587', 9),
  (96, 'UPDATE', 'User Profile', 'User rajani@123 updated profile information.', NULL, '2026-11-04 09:55:34.445228', 9),
  (97, 'UPDATE', 'User Profile', 'User hr_admin updated profile information.', NULL, '2026-11-04 10:01:20.458738', 2),
  (98, 'UPDATE', 'User Profile', 'User hr_admin updated profile information.', NULL, '2026-11-04 10:01:43.291173', 2),
  (99, 'UPDATE', 'Attendance', 'Punch-out recorded for EMP113. Total hours: 0.71', '127.0.0.1', '2026-11-04 10:35:21.277863', 9),
  (100, 'CREATE', 'Profile Corrections', 'Correction requested by EMP113 for phone no', NULL, '2026-11-04 10:37:33.047616', 9);

INSERT INTO `accounts_auditlog` (`id`, `action`, `module`, `description`, `ip_address`, `created_at`, `user_id`) VALUES
  (101, 'LOGIN', 'Demo Switcher', 'Switched active user to hr_admin (hr).', NULL, '2026-11-04 10:37:38.366264', 2),
  (102, 'APPROVAL', 'Profile Corrections', 'Approved profile change for EMP113: phone no', NULL, '2026-11-04 10:37:45.771434', 2),
  (103, 'LOGOUT', 'Authentication', 'User hr_admin logged out.', NULL, '2026-11-04 11:16:10.072285', 2),
  (104, 'LOGIN', 'Authentication', 'User rajani@123 logged in successfully.', NULL, '2026-11-04 11:16:28.327530', 9),
  (105, 'CREATE', 'Profile Corrections', 'Correction requested by EMP113 for City', NULL, '2026-11-04 11:18:10.280782', 9),
  (106, 'LOGIN', 'Demo Switcher', 'Switched active user to hr_admin (hr).', NULL, '2026-11-04 11:18:51.176990', 2),
  (107, 'APPROVAL', 'Profile Corrections', 'Approved profile change for EMP113: City (Updated city to cuttack)', NULL, '2026-11-04 11:19:07.598340', 2),
  (108, 'LOGIN', 'Authentication', 'User hr_admin logged in successfully.', NULL, '2026-11-05 02:04:09.224902', 2),
  (109, 'PAYROLL', 'Payroll Management', 'October 2026 monthly company-wide payroll processed by HR Admin Smruti Rekha Swain.', '192.168.1.10', '2026-11-05 02:15:38.254994', 2),
  (110, 'APPROVAL', 'Executive Approvals', 'October 2026 monthly payroll approved by Head of Company Debasish Mohapatra.', '192.168.1.2', '2026-11-05 02:15:38.261533', 1),
  (111, 'LOGIN', 'Authentication', 'User hr_admin logged in successfully.', NULL, '2026-11-05 02:19:29.281355', 2),
  (112, 'LOGIN', 'Authentication', 'User hr_admin logged in successfully.', NULL, '2026-11-05 09:10:49.771270', 2);


DROP TABLE IF EXISTS `django_admin_log`;
CREATE TABLE `django_admin_log` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `object_id` LONGTEXT,
  `object_repr` VARCHAR(200) NOT NULL,
  `action_flag` BIGINT NOT NULL,
  `change_message` LONGTEXT NOT NULL,
  `content_type_id` BIGINT,
  `user_id` BIGINT NOT NULL,
  `action_time` DATETIME(6) NULL NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS `organization_companypolicy`;
CREATE TABLE `organization_companypolicy` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `title` VARCHAR(200) NOT NULL,
  `category` VARCHAR(100) NOT NULL,
  `document` VARCHAR(100),
  `summary` LONGTEXT NOT NULL,
  `effective_date` DATE NULL NOT NULL,
  `requires_acknowledgement` TINYINT(1) NOT NULL,
  `created_at` DATETIME(6) NULL NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Dumping data for table `organization_companypolicy` (3 records)
INSERT INTO `organization_companypolicy` (`id`, `title`, `category`, `document`, `summary`, `effective_date`, `requires_acknowledgement`, `created_at`) VALUES
  (1, 'Code of Conduct & Workplace Ethics Policy', 'Ethics & Governance', '', 'Mandatory corporate policy defining our commitment to integrity, diversity, non-discrimination, anti-harassment, and mutual respect.', '2026-01-01', 1, '2026-11-01 15:07:14.574656'),
  (2, 'Flexible Remote & Hybrid Work Policy', 'Workplace Operations', '', 'Guidelines on core business hours, office attendance frequency, ergonomics, and communication etiquette for hybrid workers.', '2026-01-01', 0, '2026-11-01 15:07:14.583415'),
  (3, 'Information Security & Clean Desk Policy', 'IT & Data Security', '', 'Protocols on safeguarding confidential employee and client data, physical workstation security, password governance, and data classification.', '2026-01-01', 1, '2026-11-01 15:07:14.591631');


DROP TABLE IF EXISTS `organization_holiday`;
CREATE TABLE `organization_holiday` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `title` VARCHAR(150) NOT NULL,
  `holiday_type` VARCHAR(20) NOT NULL,
  `date` DATE NULL NOT NULL,
  `description` LONGTEXT NOT NULL,
  `is_optional` TINYINT(1) NOT NULL,
  `created_at` DATETIME(6) NULL NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Dumping data for table `organization_holiday` (7 records)
INSERT INTO `organization_holiday` (`id`, `title`, `holiday_type`, `date`, `description`, `is_optional`, `created_at`) VALUES
  (1, 'Republic Day', 'PUBLIC', '2026-01-26', 'National celebration of the Constitution of India.', 0, '2026-11-01 15:07:14.443709'),
  (2, 'Holi (Festival of Colours)', 'FESTIVAL', '2026-03-25', 'Spring festival celebrated nationwide.', 0, '2026-11-01 15:07:14.451552'),
  (3, 'Independence Day', 'PUBLIC', '2026-08-15', '79th Indian Independence Day celebration.', 0, '2026-11-01 15:07:14.459385'),
  (4, 'Mahatma Gandhi Jayanti', 'PUBLIC', '2026-10-02', 'Honoring the Father of the Nation.', 0, '2026-11-01 15:07:14.468956'),
  (5, 'Diwali (Deepavali)', 'FESTIVAL', '2026-11-10', 'Festival of lights and prosperity.', 0, '2026-11-01 15:07:14.477774'),
  (6, 'Christmas Day', 'FESTIVAL', '2026-12-25', 'Christmas celebrations and year-end holidays.', 0, '2026-11-01 15:07:14.485654'),
  (7, 'Company Annual Founder Day', 'COMPANY', '2026-12-31', 'Foundation Day corporate celebration.', 0, '2026-11-01 15:07:14.493936');


DROP TABLE IF EXISTS `organization_companyevent`;
CREATE TABLE `organization_companyevent` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `title` VARCHAR(200) NOT NULL,
  `event_type` VARCHAR(30) NOT NULL,
  `venue` VARCHAR(200) NOT NULL,
  `start_datetime` DATETIME(6) NULL NOT NULL,
  `end_datetime` DATETIME(6) NULL NOT NULL,
  `description` LONGTEXT NOT NULL,
  `cover_image` VARCHAR(100),
  `is_active` TINYINT(1) NOT NULL,
  `created_at` DATETIME(6) NULL NOT NULL,
  `created_by_id` BIGINT,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Dumping data for table `organization_companyevent` (2 records)
INSERT INTO `organization_companyevent` (`id`, `title`, `event_type`, `venue`, `start_datetime`, `end_datetime`, `description`, `cover_image`, `is_active`, `created_at`, `created_by_id`) VALUES
  (1, 'Annual Tech Symposium & Hackathon 2026', 'TRAINING', 'Main Auditorium, Bengaluru HQ Tech Park & Virtual Stream', '2026-11-14 00:07:14.535462', '2026-11-15 09:07:14.535480', '48-hour internal hackathon focusing on AI-assisted enterprise workflows, microservices optimization, and developer productivity tools.', '', 1, '2026-11-01 15:07:14.537558', 2),
  (2, 'Diwali Grand Corporate Celebration & Cultural Evening', 'CELEBRATION', 'Open Lawn Pavilion, Bengaluru & Campus Hubs', '2026-11-10 08:07:14.545873', '2026-11-10 13:07:14.545895', 'Traditional festive celebration featuring ethnic attire contests, musical performances, rangoli competitions, and a banquet dinner.', '', 1, '2026-11-01 15:07:14.547758', 2);


DROP TABLE IF EXISTS `organization_department`;
CREATE TABLE `organization_department` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(100) NOT NULL,
  `code` VARCHAR(20) NOT NULL,
  `description` LONGTEXT NOT NULL,
  `created_at` DATETIME(6) NULL NOT NULL,
  `head_of_department_id` BIGINT,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Dumping data for table `organization_department` (5 records)
INSERT INTO `organization_department` (`id`, `name`, `code`, `description`, `created_at`, `head_of_department_id`) VALUES
  (1, 'Engineering & Technology', 'ENG', 'Software architecture, web development, QA and DevOps.', '2026-11-01 15:07:10.136628', NULL),
  (2, 'Human Resources', 'HR', 'Talent acquisition, employee welfare, payroll, and culture.', '2026-11-01 15:07:10.142423', NULL),
  (3, 'Product & UI/UX Design', 'PROD', 'Product strategy, wireframing, UX research, and UI design.', '2026-11-01 15:07:10.146993', NULL),
  (4, 'Site Operations & Infrastructure', 'OPS', 'Facilities, workplace management, IT and compliance.', '2026-11-01 15:07:10.151846', NULL),
  (5, 'Marketing & Growth', 'MKT', 'Digital marketing, enterprise branding, sales operations.', '2026-11-01 15:07:10.157840', NULL);


DROP TABLE IF EXISTS `organization_eventgallery`;
CREATE TABLE `organization_eventgallery` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `title` VARCHAR(200) NOT NULL,
  `image` VARCHAR(100) NOT NULL,
  `caption` VARCHAR(255) NOT NULL,
  `uploaded_at` DATETIME(6) NULL NOT NULL,
  `event_id` BIGINT,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS `organization_site`;
CREATE TABLE `organization_site` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(150) NOT NULL,
  `code` VARCHAR(20) NOT NULL,
  `city` VARCHAR(100) NOT NULL,
  `address` LONGTEXT NOT NULL,
  `contact_phone` VARCHAR(20) NOT NULL,
  `is_active` TINYINT(1) NOT NULL,
  `created_at` DATETIME(6) NULL NOT NULL,
  `site_manager_id` BIGINT,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Dumping data for table `organization_site` (3 records)
INSERT INTO `organization_site` (`id`, `name`, `code`, `city`, `address`, `contact_phone`, `is_active`, `created_at`, `site_manager_id`) VALUES
  (1, 'Bengaluru HQ Tech Park', 'BLR-HQ', 'Bengaluru', 'Tower 4, Embassy Tech Village, Outer Ring Road, Bengaluru, Karnataka 560103', '+91 80 4912 3000', 1, '2026-11-01 15:07:10.198385', 3),
  (2, 'Hyderabad Innovation Campus', 'HYD-CAMPUS', 'Hyderabad', 'Mindspace Cyberabad, Building 12A, Hitech City, Hyderabad, Telangana 500081', '+91 40 6811 4500', 1, '2026-11-01 15:07:10.203133', NULL),
  (3, 'Pune Development Center', 'PUNE-DC', 'Pune', 'EON Free Zone, Kharadi, Pune, Maharashtra 411014', '+91 20 4122 8800', 1, '2026-11-01 15:07:10.207592', NULL);


DROP TABLE IF EXISTS `organization_announcement`;
CREATE TABLE `organization_announcement` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `title` VARCHAR(255) NOT NULL,
  `category` VARCHAR(20) NOT NULL,
  `priority` VARCHAR(20) NOT NULL,
  `content` LONGTEXT NOT NULL,
  `attachment` VARCHAR(100),
  `is_pinned` TINYINT(1) NOT NULL,
  `created_at` DATETIME(6) NULL NOT NULL,
  `created_by_id` BIGINT,
  `target_department_id` BIGINT,
  `target_site_id` BIGINT,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Dumping data for table `organization_announcement` (4 records)
INSERT INTO `organization_announcement` (`id`, `title`, `category`, `priority`, `content`, `attachment`, `is_pinned`, `created_at`, `created_by_id`, `target_department_id`, `target_site_id`) VALUES
  (1, 'Annual Performance Review Cycle 2026 Open', 'MANAGEMENT', 'HIGH', 'We are pleased to announce the kick-off of our Annual Performance Review Cycle. All employees and site managers are requested to complete self-appraisals and goal validations by the end of this month in the Performance module.', '', 1, '2026-11-01 15:07:14.501947', 1, NULL, NULL),
  (2, 'Comprehensive Group Health Insurance Policy Renewal', 'HR', 'MEDIUM', 'The company has renewed our corporate health coverage with upgraded parental benefits and enhanced cashless network hospitals. Please check your HRMS Document Vault for policy details and e-cards.', '', 1, '2026-11-01 15:07:14.510825', 2, NULL, NULL),
  (3, 'Bangalore HQ Office Cafeteria Upgrade & New Menu', 'GENERAL', 'LOW', 'Starting this Monday, the Bengaluru HQ cafeteria features an expanded organic salad bar, live gourmet espresso stations, and diverse regional lunch offerings.', '', 0, '2026-11-01 15:07:14.519174', 2, NULL, 1),
  (4, 'Emergency IT Security Advisory: Mandatory MFA Verification', 'EMERGENCY', 'URGENT', 'All team members must ensure two-factor authentication is active on work email accounts and VPN clients. Report any phishing anomalies to the IT Support Desk immediately.', '', 1, '2026-11-01 15:07:14.527985', 1, NULL, NULL);


DROP TABLE IF EXISTS `organization_announcementread`;
CREATE TABLE `organization_announcementread` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `read_at` DATETIME(6) NULL NOT NULL,
  `announcement_id` BIGINT NOT NULL,
  `user_id` BIGINT NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS `organization_designation`;
CREATE TABLE `organization_designation` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `title` VARCHAR(100) NOT NULL,
  `grade_level` VARCHAR(20) NOT NULL,
  `description` LONGTEXT NOT NULL,
  `department_id` BIGINT NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Dumping data for table `organization_designation` (8 records)
INSERT INTO `organization_designation` (`id`, `title`, `grade_level`, `description`, `department_id`) VALUES
  (1, 'Chief Executive Officer / Managing Director', 'EXEC-1', '', 4),
  (2, 'Head of People & HR Operations', 'L5 - Director', '', 2),
  (3, 'Site Operations Manager', 'L4 - Lead', '', 4),
  (4, 'Senior Full-Stack Software Engineer', 'L3 - Senior', '', 1),
  (5, 'Software Engineer (Backend Python)', 'L2 - Engineer', '', 1),
  (6, 'QA Automation Engineer', 'L2 - Engineer', '', 1),
  (7, 'Lead UI/UX Designer', 'L3 - Senior', '', 3),
  (8, 'Senior Full-Stack Django Developer', 'L2 - Professional', '', 1);


DROP TABLE IF EXISTS `organization_eventparticipant`;
CREATE TABLE `organization_eventparticipant` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `registered_at` DATETIME(6) NULL NOT NULL,
  `attended` TINYINT(1) NOT NULL,
  `event_id` BIGINT NOT NULL,
  `user_id` BIGINT NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Dumping data for table `organization_eventparticipant` (3 records)
INSERT INTO `organization_eventparticipant` (`id`, `registered_at`, `attended`, `event_id`, `user_id`) VALUES
  (1, '2026-11-01 15:07:14.556658', 0, 1, 4),
  (2, '2026-11-01 15:07:14.565225', 0, 2, 4),
  (3, '2026-11-04 10:35:53.869507', 0, 2, 9);


DROP TABLE IF EXISTS `organization_policyacknowledgement`;
CREATE TABLE `organization_policyacknowledgement` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `acknowledged_at` DATETIME(6) NULL NOT NULL,
  `policy_id` BIGINT NOT NULL,
  `user_id` BIGINT NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Dumping data for table `organization_policyacknowledgement` (2 records)
INSERT INTO `organization_policyacknowledgement` (`id`, `acknowledged_at`, `policy_id`, `user_id`) VALUES
  (1, '2026-11-02 10:28:19.899092', 1, 4),
  (2, '2026-11-04 11:47:27.191688', 1, 2);


DROP TABLE IF EXISTS `employees_employeeprofile`;
CREATE TABLE `employees_employeeprofile` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `emp_id` VARCHAR(20) NOT NULL,
  `employment_type` VARCHAR(20) NOT NULL,
  `joining_date` DATE NULL NOT NULL,
  `date_of_birth` DATE NULL,
  `gender` VARCHAR(20) NOT NULL,
  `marital_status` VARCHAR(20) NOT NULL,
  `blood_group` VARCHAR(10) NOT NULL,
  `personal_email` VARCHAR(254) NOT NULL,
  `address` LONGTEXT NOT NULL,
  `city` VARCHAR(100) NOT NULL,
  `state` VARCHAR(100) NOT NULL,
  `postal_code` VARCHAR(20) NOT NULL,
  `emergency_contact_name` VARCHAR(100) NOT NULL,
  `emergency_contact_relation` VARCHAR(50) NOT NULL,
  `emergency_contact_phone` VARCHAR(20) NOT NULL,
  `bank_name` VARCHAR(100) NOT NULL,
  `bank_account_number` VARCHAR(50) NOT NULL,
  `ifsc_code` VARCHAR(30) NOT NULL,
  `pan_number` VARCHAR(30) NOT NULL,
  `uan_number` VARCHAR(30) NOT NULL,
  `education_details` LONGTEXT NOT NULL,
  `experience_summary` LONGTEXT NOT NULL,
  `status` VARCHAR(20) NOT NULL,
  `show_birthday_publicly` TINYINT(1) NOT NULL,
  `created_at` DATETIME(6) NULL NOT NULL,
  `updated_at` DATETIME(6) NULL NOT NULL,
  `department_id` BIGINT,
  `designation_id` BIGINT,
  `reporting_manager_id` BIGINT,
  `site_id` BIGINT,
  `user_id` BIGINT NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Dumping data for table `employees_employeeprofile` (9 records)
INSERT INTO `employees_employeeprofile` (`id`, `emp_id`, `employment_type`, `joining_date`, `date_of_birth`, `gender`, `marital_status`, `blood_group`, `personal_email`, `address`, `city`, `state`, `postal_code`, `emergency_contact_name`, `emergency_contact_relation`, `emergency_contact_phone`, `bank_name`, `bank_account_number`, `ifsc_code`, `pan_number`, `uan_number`, `education_details`, `experience_summary`, `status`, `show_birthday_publicly`, `created_at`, `updated_at`, `department_id`, `designation_id`, `reporting_manager_id`, `site_id`, `user_id`) VALUES
  (1, 'EMP001', 'FULL_TIME', '2020-01-15', '1980-05-20', 'MALE', 'MARRIED', 'O+', '', 'Plot 42, Infocity Avenue, Chandrasekharpur, Bhubaneswar, Odisha 751024', 'Bhubaneswar', '', '', 'Subhashree Mohapatra', 'Spouse', '+91 98201 99999', 'HDFC Bank', '50100234567891', 'HDFC0001234', 'ABCPS1234F', '100902837482', '', '', 'ACTIVE', 1, '2026-11-01 15:07:14.131744', '2026-11-05 09:08:56.279281', 4, 1, NULL, 1, 1),
  (2, 'EMP002', 'FULL_TIME', '2021-03-01', '1988-11-05', 'FEMALE', 'MARRIED', 'B+', '', 'Flat 302, Royal Palms, Saheed Nagar, Bhubaneswar, Odisha 751007', 'Bhubaneswar', '', '', 'Satyajit Swain', 'Spouse', '+91 98450 11223', 'ICICI Bank', '001205012345', 'ICIC0000012', 'BNMPP8877K', '101239847291', '', '', 'ACTIVE', 1, '2026-11-01 15:07:14.141337', '2026-11-05 09:08:56.287798', 2, 2, 1, 1, 2),
  (3, 'EMP003', 'FULL_TIME', '2021-08-15', '1985-11-02', 'MALE', 'MARRIED', 'A+', '', 'B-704, Mahanadi Vihar, Cuttack, Odisha 753004', 'Cuttack', '', '', 'Sunita Jena', 'Spouse', '+91 98765 11111', 'State Bank of India', '201982736451', 'SBIN0004567', 'ASDPV3344J', '100847291834', '', '', 'ACTIVE', 1, '2026-11-01 15:07:14.150844', '2026-11-05 09:08:56.295303', 4, 3, 1, 1, 3),
  (4, 'EMP101', 'FULL_TIME', '2022-04-10', '1994-11-01', 'MALE', 'SINGLE', 'O+', '', '124, Kalinga Nagar Sector 2, Ghatikia, Bhubaneswar, Odisha 751003', 'Bhubaneswar', '', '', 'Pradeep Kumar Sahoo', 'Father', '+91 99001 99999', 'HDFC Bank', '50100492817349', 'HDFC0001827', 'DOEPJ1234Q', '101928374655', 'B.Tech in Computer Science & Engineering (2012-2016)', '8+ years in full-stack architecture, Django, Python, PostgreSQL, and cloud deployments.', 'ACTIVE', 1, '2026-11-01 15:07:14.159293', '2026-11-05 09:08:56.302617', 1, 4, 3, 1, 4),
  (5, 'EMP102', 'FULL_TIME', '2023-01-05', '1992-11-14', 'FEMALE', 'SINGLE', 'AB+', '', '45, Master Canteen Square, Station Area, Bhubaneswar, Odisha 751001', 'Bhubaneswar', '', '', 'Gitanjali Mishra', 'Mother', '+91 98111 11223', 'Axis Bank', '918020038472918', 'UTIB0000213', 'CNRPJ9988X', '101827364512', '', '', 'ACTIVE', 1, '2026-11-01 15:07:14.167735', '2026-11-05 09:08:56.309860', 3, 7, 3, 1, 5),
  (6, 'EMP103', 'FULL_TIME', '2023-07-10', '1996-12-01', 'FEMALE', 'SINGLE', 'B+', '', 'Sector 5, Rourkela Steel City, Odisha 769002', 'Rourkela', '', '', 'Ramesh Chandra Behera', 'Father', '+91 97234 11122', 'HDFC Bank', '50100772211990', 'HDFC0000456', 'PTLPK6655M', '101928471625', '', '', 'ACTIVE', 1, '2026-11-01 15:07:14.176350', '2026-11-05 09:08:56.316436', 1, 6, 3, 2, 6),
  (7, 'EMP104', 'FULL_TIME', '2024-02-01', '1997-08-22', 'MALE', 'SINGLE', 'O-', '', 'Engineering School Road, Berhampur, Ganjam, Odisha 760010', 'Berhampur', '', '', 'Priyadarshini Rout', 'Sister', '+91 98401 22334', 'Kotak Mahindra Bank', '411002938472', 'KKBK0000123', 'MLRDK3322L', '102938475612', '', '', 'ACTIVE', 1, '2026-11-01 15:07:14.185288', '2026-11-05 09:08:56.323136', 1, 5, 3, 3, 7),
  (8, 'EMP112', 'FULL_TIME', '2026-11-02', '2005-06-04', 'MALE', 'SINGLE', 'o+', 'slipu061@gmail.com', 'tyru', 'Bhubaneswar', 'Odisha', '234566', '9876543212', 'daughter', '+913456787898', 'hdfc', 'axcdsvfrc667775654545609', 'hdfc565465456654', 'asfdc987898v', '', '', '', 'ACTIVE', 1, '2026-11-02 12:30:58.480947', '2026-11-02 12:30:58.480973', 1, 8, NULL, 1, 8),
  (9, 'EMP113', 'FULL_TIME', '2026-08-12', '2000-06-11', 'MALE', 'SINGLE', 'o+', '', 'tyru', 'cuttack', '', '765434', 'rani kumar', 'daughter', '9876543212', 'SBI', '9867658767', 'HDFC0001234', 'ASFDE1234F', '877788987888', 'b.tech', 'experiences', 'ACTIVE', 1, '2026-11-04 09:50:37.231608', '2026-11-04 09:50:37.231637', 1, 4, 2, 3, 9);


DROP TABLE IF EXISTS `employees_employeedocument`;
CREATE TABLE `employees_employeedocument` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `doc_type` VARCHAR(30) NOT NULL,
  `title` VARCHAR(200) NOT NULL,
  `file` VARCHAR(100) NOT NULL,
  `uploaded_at` DATETIME(6) NULL NOT NULL,
  `employee_id` BIGINT NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS `employees_profilecorrectionrequest`;
CREATE TABLE `employees_profilecorrectionrequest` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `field_name` VARCHAR(100) NOT NULL,
  `current_value` LONGTEXT NOT NULL,
  `proposed_value` LONGTEXT NOT NULL,
  `reason` LONGTEXT NOT NULL,
  `status` VARCHAR(20) NOT NULL,
  `review_notes` LONGTEXT NOT NULL,
  `reviewed_at` DATETIME(6) NULL,
  `created_at` DATETIME(6) NULL NOT NULL,
  `employee_id` BIGINT NOT NULL,
  `reviewed_by_id` BIGINT,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Dumping data for table `employees_profilecorrectionrequest` (2 records)
INSERT INTO `employees_profilecorrectionrequest` (`id`, `field_name`, `current_value`, `proposed_value`, `reason`, `status`, `review_notes`, `reviewed_at`, `created_at`, `employee_id`, `reviewed_by_id`) VALUES
  (1, 'phone no', '8765342345', '9876543234', 'chnaged plese', 'APPROVED', '', '2026-11-04 10:37:45.762806', '2026-11-04 10:37:33.038996', 9, 2),
  (2, 'City', 'bhubaneswar', 'cuttack', 'now i shift to cuttack', 'APPROVED', 'Updated city to cuttack', '2026-11-04 11:19:07.589892', '2026-11-04 11:18:10.267335', 9, 2);


DROP TABLE IF EXISTS `attendance_shift`;
CREATE TABLE `attendance_shift` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(100) NOT NULL,
  `start_time` TIME(6) NULL NOT NULL,
  `end_time` TIME(6) NULL NOT NULL,
  `grace_period_minutes` BIGINT NOT NULL,
  `half_day_hours` DECIMAL NOT NULL,
  `full_day_hours` DECIMAL NOT NULL,
  `is_default` TINYINT(1) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Dumping data for table `attendance_shift` (2 records)
INSERT INTO `attendance_shift` (`id`, `name`, `start_time`, `end_time`, `grace_period_minutes`, `half_day_hours`, `full_day_hours`, `is_default`) VALUES
  (1, 'General Shift', '09:00:00', '18:00:00', 15, 4.5, 8, 1),
  (2, 'Morning Shift', '08:00:00', '17:00:00', 15, 4.5, 8, 0);


DROP TABLE IF EXISTS `attendance_attendance`;
CREATE TABLE `attendance_attendance` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `date` DATE NULL NOT NULL,
  `punch_in` DATETIME(6) NULL,
  `punch_out` DATETIME(6) NULL,
  `working_hours` DECIMAL NOT NULL,
  `break_duration_minutes` BIGINT NOT NULL,
  `status` VARCHAR(20) NOT NULL,
  `is_late` TINYINT(1) NOT NULL,
  `is_early_departure` TINYINT(1) NOT NULL,
  `overtime_hours` DECIMAL NOT NULL,
  `punch_in_ip` LONGTEXT,
  `punch_out_ip` LONGTEXT,
  `device_source` VARCHAR(20) NOT NULL,
  `notes` LONGTEXT NOT NULL,
  `employee_id` BIGINT NOT NULL,
  `shift_id` BIGINT,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Dumping data for table `attendance_attendance` (34 records)
INSERT INTO `attendance_attendance` (`id`, `date`, `punch_in`, `punch_out`, `working_hours`, `break_duration_minutes`, `status`, `is_late`, `is_early_departure`, `overtime_hours`, `punch_in_ip`, `punch_out_ip`, `device_source`, `notes`, `employee_id`, `shift_id`) VALUES
  (1, '2026-11-01', '2026-11-01 09:02:00', '2026-11-01 17:06:19.574601', 8.07, 0, 'PRESENT', 0, 0, 0.07, '192.168.1.45', '127.0.0.1', 'WEB', '', 4, 1),
  (2, '2026-11-01', '2026-11-01 09:25:00.694565', NULL, 6.1, 0, 'PRESENT', 1, 0, 0, '192.168.1.88', NULL, 'WEB', 'Traffic delay at Silk Board junction.', 5, 1),
  (3, '2026-11-01', '2026-11-01 08:55:00.703081', NULL, 6.6, 0, 'PRESENT', 0, 0, 0, '10.20.4.12', NULL, 'KIOSK', '', 6, 1),
  (4, '2026-11-01', '2026-11-01 09:05:00', NULL, 0, 0, 'ON_LEAVE', 0, 0, 0, NULL, NULL, 'WEB', 'Approved Casual Leave.', 7, 1),
  (5, '2026-10-31', '2026-10-31 09:10:00.722398', '2026-10-31 17:55:00.722398', 8.75, 0, 'PRESENT', 0, 0, 0.75, NULL, NULL, 'WEB', '', 4, 1),
  (6, '2026-10-30', '2026-10-30 09:10:00.732117', '2026-10-30 17:55:00.732117', 8.75, 0, 'PRESENT', 0, 0, 0.75, NULL, NULL, 'WEB', '', 4, 1),
  (7, '2026-10-29', '2026-10-29 09:10:00.740767', '2026-10-29 17:55:00.740767', 8.75, 0, 'PRESENT', 0, 0, 0.75, NULL, NULL, 'WEB', '', 4, 1),
  (8, '2026-10-28', '2026-10-28 09:10:00.748844', '2026-10-28 17:55:00.748844', 8.75, 0, 'PRESENT', 0, 0, 0.75, NULL, NULL, 'WEB', '', 4, 1),
  (9, '2026-10-27', '2026-10-27 09:10:00.756355', '2026-10-27 17:55:00.756355', 8.75, 0, 'PRESENT', 0, 0, 0.75, NULL, NULL, 'WEB', '', 4, 1),
  (10, '2026-10-28', '2026-10-28 09:05:14.764261', '2026-10-28 17:35:14.764261', 8.5, 0, 'PRESENT', 0, 0, 0.5, NULL, NULL, 'WEB', '', 7, 1),
  (11, '2026-11-02', '2026-11-01 18:58:13.675893', NULL, 0, 0, 'PRESENT', 0, 0, 0, '127.0.0.1', NULL, 'WEB', '', 3, 1),
  (12, '2026-11-02', '2026-11-02 10:26:47.466941', '2026-11-02 10:26:49.739219', 0, 0, 'ABSENT', 1, 0, 0, '127.0.0.1', '127.0.0.1', 'WEB', '', 4, 1),
  (13, '2026-11-06', NULL, NULL, 0, 0, 'ON_LEAVE', 0, 0, 0, NULL, NULL, 'WEB', 'Approved Casual Leave', 4, NULL),
  (14, '2026-11-07', NULL, NULL, 0, 0, 'ON_LEAVE', 0, 0, 0, NULL, NULL, 'WEB', 'Approved Casual Leave', 4, NULL),
  (15, '2026-11-02', '2026-11-02 09:25:00.316192', NULL, 6.1, 0, 'PRESENT', 1, 0, 0, '192.168.1.88', NULL, 'WEB', 'Traffic delay at Silk Board junction.', 5, 1),
  (16, '2026-11-02', '2026-11-02 08:55:00.321683', NULL, 6.6, 0, 'PRESENT', 0, 0, 0, '10.20.4.12', NULL, 'KIOSK', '', 6, 1),
  (17, '2026-11-02', NULL, NULL, 0, 0, 'ON_LEAVE', 0, 0, 0, NULL, NULL, 'WEB', 'Approved Casual Leave.', 7, 1),
  (18, '2026-10-29', '2026-10-29 09:05:56.335095', NULL, 4, 0, 'HALF_DAY', 0, 0, 0, NULL, NULL, 'WEB', '', 7, 1),
  (19, '2026-11-03', '2026-11-03 09:02:00', NULL, 6.5, 0, 'PRESENT', 0, 0, 0, '192.168.1.45', NULL, 'WEB', '', 4, 1),
  (20, '2026-11-03', '2026-11-03 09:25:00.440322', NULL, 6.1, 0, 'PRESENT', 1, 0, 0, '192.168.1.88', NULL, 'WEB', 'Traffic delay at Silk Board junction.', 5, 1),
  (21, '2026-11-03', '2026-11-03 08:55:00.446335', NULL, 6.6, 0, 'PRESENT', 0, 0, 0, '10.20.4.12', NULL, 'KIOSK', '', 6, 1),
  (22, '2026-11-03', NULL, NULL, 0, 0, 'ON_LEAVE', 0, 0, 0, NULL, NULL, 'WEB', 'Approved Casual Leave.', 7, 1),
  (23, '2026-10-30', '2026-10-30 09:05:54.461967', '2026-10-30 17:35:54.461967', 8.5, 0, 'PRESENT', 0, 0, 0.5, NULL, NULL, 'WEB', '', 7, 1),
  (24, '2026-11-03', '2026-11-03 06:14:03.780971', NULL, 0, 0, 'PRESENT', 1, 0, 0, '127.0.0.1', NULL, 'WEB', '', 1, 1),
  (25, '2026-11-04', '2026-11-04 09:02:00', NULL, 6.5, 0, 'PRESENT', 0, 0, 0, '192.168.1.45', NULL, 'WEB', '', 4, 1),
  (26, '2026-11-04', '2026-11-04 09:25:00.696804', NULL, 6.1, 0, 'PRESENT', 1, 0, 0, '192.168.1.88', NULL, 'WEB', 'Traffic delay at Silk Board junction.', 5, 1),
  (27, '2026-11-04', '2026-11-04 08:55:00.702096', NULL, 6.6, 0, 'PRESENT', 0, 0, 0, '10.20.4.12', NULL, 'KIOSK', '', 6, 1),
  (28, '2026-11-04', NULL, NULL, 0, 0, 'ON_LEAVE', 0, 0, 0, NULL, NULL, 'WEB', 'Approved Casual Leave.', 7, 1),
  (29, '2026-10-31', '2026-10-31 09:05:36.717208', NULL, 4, 0, 'HALF_DAY', 0, 0, 0, NULL, NULL, 'WEB', '', 7, 1),
  (30, '2026-11-04', '2026-11-04 09:52:51.240887', '2026-11-04 10:35:21.265078', 0.71, 0, 'ABSENT', 1, 0, 0, '127.0.0.1', '127.0.0.1', 'WEB', '', 9, 1),
  (31, '2026-11-05', '2026-11-05 09:02:00', NULL, 6.5, 0, 'PRESENT', 0, 0, 0, '192.168.1.45', NULL, 'WEB', '', 4, 1),
  (32, '2026-11-05', '2026-11-05 09:25:00.626041', NULL, 6.1, 0, 'PRESENT', 1, 0, 0, '192.168.1.88', NULL, 'WEB', 'Traffic delay at Silk Board junction.', 5, 1),
  (33, '2026-11-05', '2026-11-05 08:55:00.632953', NULL, 6.6, 0, 'PRESENT', 0, 0, 0, '10.20.4.12', NULL, 'KIOSK', '', 6, 1),
  (34, '2026-11-05', NULL, NULL, 0, 0, 'ON_LEAVE', 0, 0, 0, NULL, NULL, 'WEB', 'Approved Casual Leave.', 7, 1);


DROP TABLE IF EXISTS `attendance_attendanceauditlog`;
CREATE TABLE `attendance_attendanceauditlog` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `action` VARCHAR(100) NOT NULL,
  `previous_data` LONGTEXT NOT NULL,
  `new_data` LONGTEXT NOT NULL,
  `reason` LONGTEXT NOT NULL,
  `timestamp` DATETIME(6) NULL NOT NULL,
  `attendance_id` BIGINT NOT NULL,
  `changed_by_id` BIGINT,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Dumping data for table `attendance_attendanceauditlog` (2 records)
INSERT INTO `attendance_attendanceauditlog` (`id`, `action`, `previous_data`, `new_data`, `reason`, `timestamp`, `attendance_id`, `changed_by_id`) VALUES
  (1, 'CORRECTION_APPROVED', '', '', 'Accidental omission of punch out due to emergency client release call at 6:00 PM.', '2026-11-02 12:11:18.981531', 10, 2),
  (2, 'CORRECTION_APPROVED', '', '', 'Accidental omission of punch out due to emergency client release call at 6:00 PM.', '2026-11-03 06:04:19.356531', 23, 2);


DROP TABLE IF EXISTS `attendance_attendancecorrectionrequest`;
CREATE TABLE `attendance_attendancecorrectionrequest` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `date` DATE NULL NOT NULL,
  `requested_punch_in` DATETIME(6) NULL,
  `requested_punch_out` DATETIME(6) NULL,
  `reason` LONGTEXT NOT NULL,
  `status` VARCHAR(20) NOT NULL,
  `review_notes` LONGTEXT NOT NULL,
  `reviewed_at` DATETIME(6) NULL,
  `created_at` DATETIME(6) NULL NOT NULL,
  `attendance_id` BIGINT,
  `employee_id` BIGINT NOT NULL,
  `reviewed_by_id` BIGINT,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Dumping data for table `attendance_attendancecorrectionrequest` (5 records)
INSERT INTO `attendance_attendancecorrectionrequest` (`id`, `date`, `requested_punch_in`, `requested_punch_out`, `reason`, `status`, `review_notes`, `reviewed_at`, `created_at`, `attendance_id`, `employee_id`, `reviewed_by_id`) VALUES
  (1, '2026-10-28', '2026-10-28 09:05:14.764261', '2026-10-28 17:35:14.764261', 'Accidental omission of punch out due to emergency client release call at 6:00 PM.', 'APPROVED', '', '2026-11-02 12:11:18.917225', '2026-11-01 15:07:14.774060', 10, 7, 2),
  (2, '2026-10-29', '2026-10-29 09:05:56.335095', '2026-10-29 17:35:56.335095', 'Accidental omission of punch out due to emergency client release call at 6:00 PM.', 'REJECTED', '', '2026-11-02 13:16:48.361950', '2026-11-02 13:13:56.341600', 18, 7, 2),
  (3, '2026-10-30', '2026-10-30 09:05:54.461967', '2026-10-30 17:35:54.461967', 'Accidental omission of punch out due to emergency client release call at 6:00 PM.', 'APPROVED', '', '2026-11-03 06:04:19.340358', '2026-11-03 04:15:54.468490', 23, 7, 2),
  (4, '2026-10-31', '2026-10-31 09:05:36.717208', '2026-10-31 17:35:36.717208', 'Accidental omission of punch out due to emergency client release call at 6:00 PM.', 'PENDING', '', NULL, '2026-11-04 04:29:36.724963', 29, 7, NULL),
  (5, '2026-11-01', '2026-11-01 09:05:00', '2026-11-01 17:35:00', 'Accidental omission of punch out due to emergency client release call at 6:00 PM.', 'PENDING', '', NULL, '2026-11-05 02:15:38.228419', 4, 7, NULL);


DROP TABLE IF EXISTS `leave_management_leavetype`;
CREATE TABLE `leave_management_leavetype` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(100) NOT NULL,
  `code` VARCHAR(20) NOT NULL,
  `days_per_year` DECIMAL NOT NULL,
  `is_paid` TINYINT(1) NOT NULL,
  `requires_attachment` TINYINT(1) NOT NULL,
  `description` LONGTEXT NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Dumping data for table `leave_management_leavetype` (4 records)
INSERT INTO `leave_management_leavetype` (`id`, `name`, `code`, `days_per_year`, `is_paid`, `requires_attachment`, `description`) VALUES
  (1, 'Casual Leave', 'CL', 12, 1, 0, 'For unplanned personal affairs, casual events.'),
  (2, 'Sick Leave', 'SL', 10, 1, 1, 'Medical illness or health consultations.'),
  (3, 'Earned / Privilege Leave', 'EL', 15, 1, 0, 'Planned vacations and annual rest leaves.'),
  (4, 'Loss of Pay (Unpaid Leave)', 'LOP', 0, 0, 0, 'Leaves taken without paid quota balance.');


DROP TABLE IF EXISTS `leave_management_leaverequest`;
CREATE TABLE `leave_management_leaverequest` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `start_date` DATE NULL NOT NULL,
  `end_date` DATE NULL NOT NULL,
  `is_half_day` TINYINT(1) NOT NULL,
  `half_day_period` VARCHAR(20) NOT NULL,
  `total_days` DECIMAL NOT NULL,
  `reason` LONGTEXT NOT NULL,
  `attachment` VARCHAR(100),
  `status` VARCHAR(25) NOT NULL,
  `manager_decision` VARCHAR(20) NOT NULL,
  `manager_remarks` LONGTEXT NOT NULL,
  `manager_action_at` DATETIME(6) NULL,
  `hr_decision` VARCHAR(20) NOT NULL,
  `hr_remarks` LONGTEXT NOT NULL,
  `hr_action_at` DATETIME(6) NULL,
  `applied_at` DATETIME(6) NULL NOT NULL,
  `updated_at` DATETIME(6) NULL NOT NULL,
  `employee_id` BIGINT NOT NULL,
  `hr_action_by_id` BIGINT,
  `manager_action_by_id` BIGINT,
  `leave_type_id` BIGINT NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Dumping data for table `leave_management_leaverequest` (15 records)
INSERT INTO `leave_management_leaverequest` (`id`, `start_date`, `end_date`, `is_half_day`, `half_day_period`, `total_days`, `reason`, `attachment`, `status`, `manager_decision`, `manager_remarks`, `manager_action_at`, `hr_decision`, `hr_remarks`, `hr_action_at`, `applied_at`, `updated_at`, `employee_id`, `hr_action_by_id`, `manager_action_by_id`, `leave_type_id`) VALUES
  (1, '2026-11-06', '2026-11-07', 0, '', 2, 'Attending family celebration and personal commitments.', '', 'APPROVED', 'PENDING', '', NULL, 'APPROVED', '', '2026-11-02 12:12:43.460495', '2026-11-01 15:07:14.414558', '2026-11-02 12:12:43.461094', 4, 2, NULL, 1),
  (2, '2026-11-11', '2026-11-13', 0, '', 3, 'Annual family vacation trip to Himachal.', '', 'REJECTED', 'RECOMMENDED', 'Team workload covered by Priya and David. Recommended.', '2026-10-31 15:07:14.422021', 'REJECTED', '', '2026-11-02 12:12:39.080395', '2026-11-01 15:07:14.424077', '2026-11-02 12:12:39.080701', 5, 2, 3, 3),
  (3, '2026-10-18', '2026-10-18', 0, '', 1, 'Viral fever and doctor consultation.', '', 'APPROVED', 'RECOMMENDED', '', NULL, 'APPROVED', 'Approved as per medical certificate.', '2026-10-19 15:07:14.432231', '2026-11-01 15:07:14.434448', '2026-11-01 15:07:14.434463', 7, 2, 3, 2),
  (4, '2026-11-07', '2026-11-08', 0, '', 2, 'Attending family celebration and personal commitments.', '', 'REJECTED', 'PENDING', '', NULL, 'REJECTED', '', '2026-11-02 13:16:55.523610', '2026-11-02 13:13:56.288111', '2026-11-02 13:16:55.523780', 4, 2, NULL, 1),
  (5, '2026-11-12', '2026-11-14', 0, '', 3, 'Annual family vacation trip to Himachal.', '', 'REJECTED', 'RECOMMENDED', 'Team workload covered by Priya and David. Recommended.', '2026-11-01 13:13:56.292571', 'REJECTED', '', '2026-11-02 13:16:56.747743', '2026-11-02 13:13:56.293383', '2026-11-02 13:16:56.747847', 5, 2, 3, 3),
  (6, '2026-10-19', '2026-10-19', 0, '', 1, 'Viral fever and doctor consultation.', '', 'APPROVED', 'RECOMMENDED', '', NULL, 'APPROVED', 'Approved as per medical certificate.', '2026-10-20 13:13:56.297121', '2026-11-02 13:13:56.298220', '2026-11-02 13:13:56.298230', 7, 2, 3, 2),
  (7, '2026-11-08', '2026-11-09', 0, '', 2, 'Attending family celebration and personal commitments.', '', 'PENDING_MANAGER', 'PENDING', '', NULL, 'PENDING', '', NULL, '2026-11-03 04:15:54.399328', '2026-11-03 04:15:54.399344', 4, NULL, NULL, 1),
  (8, '2026-11-13', '2026-11-15', 0, '', 3, 'Annual family vacation trip to Himachal.', '', 'PENDING_HR', 'RECOMMENDED', 'Team workload covered by Priya and David. Recommended.', '2026-11-02 04:15:54.404751', 'PENDING', '', NULL, '2026-11-03 04:15:54.405989', '2026-11-03 04:15:54.405997', 5, NULL, 3, 3),
  (9, '2026-10-20', '2026-10-20', 0, '', 1, 'Viral fever and doctor consultation.', '', 'APPROVED', 'RECOMMENDED', '', NULL, 'APPROVED', 'Approved as per medical certificate.', '2026-10-21 04:15:54.411340', '2026-11-03 04:15:54.412467', '2026-11-03 04:15:54.412475', 7, 2, 3, 2),
  (10, '2026-11-09', '2026-11-10', 0, '', 2, 'Attending family celebration and personal commitments.', '', 'PENDING_MANAGER', 'PENDING', '', NULL, 'PENDING', '', NULL, '2026-11-04 04:29:36.645906', '2026-11-04 04:29:36.645925', 4, NULL, NULL, 1),
  (11, '2026-11-14', '2026-11-16', 0, '', 3, 'Annual family vacation trip to Himachal.', '', 'PENDING_HR', 'RECOMMENDED', 'Team workload covered by Priya and David. Recommended.', '2026-11-03 04:29:36.651973', 'PENDING', '', NULL, '2026-11-04 04:29:36.653507', '2026-11-04 04:29:36.653518', 5, NULL, 3, 3),
  (12, '2026-10-21', '2026-10-21', 0, '', 1, 'Viral fever and doctor consultation.', '', 'APPROVED', 'RECOMMENDED', '', NULL, 'APPROVED', 'Approved as per medical certificate.', '2026-10-22 04:29:36.658980', '2026-11-04 04:29:36.660743', '2026-11-04 04:29:36.660753', 7, 2, 3, 2),
  (13, '2026-11-10', '2026-11-11', 0, '', 2, 'Attending family celebration and personal commitments.', '', 'PENDING_MANAGER', 'PENDING', '', NULL, 'PENDING', '', NULL, '2026-11-05 01:59:36.572597', '2026-11-05 01:59:36.572614', 4, NULL, NULL, 1),
  (14, '2026-11-15', '2026-11-17', 0, '', 3, 'Annual family vacation trip to Himachal.', '', 'PENDING_HR', 'RECOMMENDED', 'Team workload covered by Priya and David. Recommended.', '2026-11-04 01:59:36.580272', 'PENDING', '', NULL, '2026-11-05 01:59:36.581522', '2026-11-05 01:59:36.581529', 5, NULL, 3, 3),
  (15, '2026-10-22', '2026-10-22', 0, '', 1, 'Viral fever and doctor consultation.', '', 'APPROVED', 'RECOMMENDED', '', NULL, 'APPROVED', 'Approved as per medical certificate.', '2026-10-23 01:59:36.586553', '2026-11-05 01:59:36.587689', '2026-11-05 01:59:36.587697', 7, 2, 3, 2);


DROP TABLE IF EXISTS `leave_management_leavebalance`;
CREATE TABLE `leave_management_leavebalance` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `year` BIGINT NOT NULL,
  `allocated_days` DECIMAL NOT NULL,
  `used_days` DECIMAL NOT NULL,
  `pending_days` DECIMAL NOT NULL,
  `employee_id` BIGINT NOT NULL,
  `leave_type_id` BIGINT NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Dumping data for table `leave_management_leavebalance` (21 records)
INSERT INTO `leave_management_leavebalance` (`id`, `year`, `allocated_days`, `used_days`, `pending_days`, `employee_id`, `leave_type_id`) VALUES
  (1, 2026, 12, 2, 0, 1, 1),
  (2, 2026, 10, 1, 0, 1, 2),
  (3, 2026, 15, 3, 0, 1, 3),
  (4, 2026, 12, 2, 0, 2, 1),
  (5, 2026, 10, 1, 0, 2, 2),
  (6, 2026, 15, 3, 0, 2, 3),
  (7, 2026, 12, 2, 0, 3, 1),
  (8, 2026, 10, 1, 0, 3, 2),
  (9, 2026, 15, 3, 0, 3, 3),
  (10, 2026, 12, 4, 0, 4, 1),
  (11, 2026, 10, 1, 0, 4, 2),
  (12, 2026, 15, 3, 0, 4, 3),
  (13, 2026, 12, 2, 0, 5, 1),
  (14, 2026, 10, 1, 0, 5, 2),
  (15, 2026, 15, 3, 0, 5, 3),
  (16, 2026, 12, 2, 0, 6, 1),
  (17, 2026, 10, 1, 0, 6, 2),
  (18, 2026, 15, 3, 0, 6, 3),
  (19, 2026, 12, 2, 0, 7, 1),
  (20, 2026, 10, 1, 0, 7, 2),
  (21, 2026, 15, 3, 0, 7, 3);


DROP TABLE IF EXISTS `notifications_notification`;
CREATE TABLE `notifications_notification` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `title` VARCHAR(200) NOT NULL,
  `message` LONGTEXT NOT NULL,
  `notification_type` VARCHAR(20) NOT NULL,
  `target_url` VARCHAR(255) NOT NULL,
  `is_read` TINYINT(1) NOT NULL,
  `created_at` DATETIME(6) NULL NOT NULL,
  `recipient_id` BIGINT NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Dumping data for table `notifications_notification` (19 records)
INSERT INTO `notifications_notification` (`id`, `title`, `message`, `notification_type`, `target_url`, `is_read`, `created_at`, `recipient_id`) VALUES
  (1, '🎉 Happy Birthday, John!', 'The entire company family wishes you a fabulous birthday and a stellar year of success, health, and happiness!', 'BIRTHDAY', '/portal/', 0, '2026-11-01 15:07:14.858878', 4),
  (2, 'October 2026 Payslip Available', 'Your salary for October 2026 has been processed and disbursed. Click to view or download your detailed PDF payslip.', 'PAYROLL', '/payroll/my-payslips/', 0, '2026-11-01 15:07:14.867646', 4),
  (3, 'New Company Announcement: Annual Tech Symposium', 'Registrations are now open for the Annual Tech Symposium & Hackathon 2026. Register your squad!', 'EVENT', '/portal/events/', 1, '2026-11-01 15:07:14.875209', 4),
  (4, 'Action Required: 1 New Leave Request', 'John Doe (EMP101) has applied for 2 days Casual Leave starting next week.', 'LEAVE', '/dashboard/site-manager/leave-approvals/', 0, '2026-11-01 15:07:14.884391', 3),
  (5, 'Attendance Correction Request', 'David Miller has submitted a missing punch out correction for your review.', 'ATTENDANCE', '/dashboard/site-manager/attendance-corrections/', 0, '2026-11-01 15:07:14.893814', 3),
  (6, 'Leave Request Forwarded by Site Manager', 'Sarah Connor (EMP102) Earned Leave request recommended by Site Manager Rajesh Verma. Awaiting HR approval.', 'LEAVE', '/dashboard/hr/leave-requests/', 1, '2026-11-01 15:07:14.902083', 2),
  (7, 'New Candidate Application: alex kumar', 'alex kumar applied for Senior Full-Stack Django Developer via recruitment link \'nbbb\'.', 'SYSTEM', '/hr/candidates/5/', 1, '2026-11-02 12:04:43.220206', 1),
  (8, 'New Candidate Application: alex kumar', 'alex kumar applied for Senior Full-Stack Django Developer via recruitment link \'nbbb\'.', 'SYSTEM', '/hr/candidates/5/', 1, '2026-11-02 12:04:43.229721', 2),
  (9, 'Attendance Correction Approved', 'Your attendance correction request for 2026-10-28 has been approved.', 'ATTENDANCE', '/attendance/my/', 0, '2026-11-02 12:11:18.993953', 7),
  (10, 'Leave Request Rejected', 'Your Earned / Privilege Leave application was rejected. Reason: ', 'LEAVE', '/leave/my/', 0, '2026-11-02 12:12:39.118028', 5),
  (11, '🎉 Leave Request Approved!', 'Your Casual Leave application (2026-11-06 to 2026-11-07) has been approved.', 'LEAVE', '/leave/my/', 0, '2026-11-02 12:12:43.546700', 4),
  (12, 'Attendance Correction Rejected', 'Your attendance correction request for 2026-10-29 was rejected. Note: ', 'ATTENDANCE', '/attendance/my/', 0, '2026-11-02 13:16:48.375808', 7),
  (13, 'Leave Request Rejected', 'Your Casual Leave application was rejected. Reason: ', 'LEAVE', '/leave/my/', 0, '2026-11-02 13:16:55.553891', 4),
  (14, 'Leave Request Rejected', 'Your Earned / Privilege Leave application was rejected. Reason: ', 'LEAVE', '/leave/my/', 0, '2026-11-02 13:16:56.771607', 5),
  (15, 'Attendance Correction Approved', 'Your attendance correction request for 2026-10-30 has been approved.', 'ATTENDANCE', '/attendance/my/', 0, '2026-11-03 06:04:19.361987', 7),
  (16, 'New Candidate Application: arti sha', 'arti sha applied for django developer. via Universal Application Portal.', 'SYSTEM', '/hr/candidates/6/', 0, '2026-11-03 10:17:00.655208', 1),
  (17, 'New Candidate Application: arti sha', 'arti sha applied for django developer. via Universal Application Portal.', 'SYSTEM', '/hr/candidates/6/', 1, '2026-11-03 10:17:00.660854', 2),
  (18, 'Profile Correction Approved', 'Your profile correction request for \'City\' has been approved and applied to your profile.', 'SYSTEM', '/employees/EMP113/', 0, '2026-11-04 11:19:07.610420', 9),
  (19, '🎉 Happy Birthday, Soumya!', 'The entire company family wishes you a fabulous birthday and a stellar year of success, health, and happiness!', 'BIRTHDAY', '/portal/', 0, '2026-11-05 02:15:38.243970', 4);


DROP TABLE IF EXISTS `payroll_payrollperiod`;
CREATE TABLE `payroll_payrollperiod` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `month` BIGINT NOT NULL,
  `year` BIGINT NOT NULL,
  `working_days` BIGINT NOT NULL,
  `status` VARCHAR(20) NOT NULL,
  `total_gross` DECIMAL NOT NULL,
  `total_deductions` DECIMAL NOT NULL,
  `total_net` DECIMAL NOT NULL,
  `processed_at` DATETIME(6) NULL NOT NULL,
  `approved_at` DATETIME(6) NULL,
  `approved_by_id` BIGINT,
  `processed_by_id` BIGINT,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Dumping data for table `payroll_payrollperiod` (1 records)
INSERT INTO `payroll_payrollperiod` (`id`, `month`, `year`, `working_days`, `status`, `total_gross`, `total_deductions`, `total_net`, `processed_at`, `approved_at`, `approved_by_id`, `processed_by_id`) VALUES
  (1, 10, 2026, 26, 'APPROVED', 520000, 65000, 455000, '2026-11-01 15:07:14.656561', '2026-10-30 15:07:14.654582', 1, 2);


DROP TABLE IF EXISTS `payroll_salarystructure`;
CREATE TABLE `payroll_salarystructure` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `basic_salary` DECIMAL NOT NULL,
  `hra` DECIMAL NOT NULL,
  `conveyance_allowance` DECIMAL NOT NULL,
  `medical_allowance` DECIMAL NOT NULL,
  `special_allowance` DECIMAL NOT NULL,
  `provident_fund` DECIMAL NOT NULL,
  `professional_tax` DECIMAL NOT NULL,
  `tds` DECIMAL NOT NULL,
  `is_active` TINYINT(1) NOT NULL,
  `updated_at` DATETIME(6) NULL NOT NULL,
  `employee_id` BIGINT NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Dumping data for table `payroll_salarystructure` (5 records)
INSERT INTO `payroll_salarystructure` (`id`, `basic_salary`, `hra`, `conveyance_allowance`, `medical_allowance`, `special_allowance`, `provident_fund`, `professional_tax`, `tds`, `is_active`, `updated_at`, `employee_id`) VALUES
  (1, 60000, 30000, 5000, 5000, 20000, 7200, 200, 8500, 1, '2026-11-01 15:07:14.618548', 4),
  (2, 47500, 23750, 4000, 4000, 15750, 5700, 200, 5500, 1, '2026-11-01 15:07:14.626142', 5),
  (3, 40000, 20000, 3500, 3500, 13000, 4800, 200, 4000, 1, '2026-11-01 15:07:14.633547', 6),
  (4, 37500, 18750, 3500, 3500, 11750, 4500, 200, 3500, 1, '2026-11-01 15:07:14.640785', 7),
  (5, 75000, 37500, 6000, 6000, 25500, 9000, 200, 14500, 1, '2026-11-01 15:07:14.648060', 3);


DROP TABLE IF EXISTS `payroll_payslip`;
CREATE TABLE `payroll_payslip` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `month` BIGINT NOT NULL,
  `year` BIGINT NOT NULL,
  `total_working_days` DECIMAL NOT NULL,
  `present_days` DECIMAL NOT NULL,
  `paid_leaves` DECIMAL NOT NULL,
  `loss_of_pay_days` DECIMAL NOT NULL,
  `payable_days` DECIMAL NOT NULL,
  `basic_salary` DECIMAL NOT NULL,
  `hra` DECIMAL NOT NULL,
  `conveyance_allowance` DECIMAL NOT NULL,
  `medical_allowance` DECIMAL NOT NULL,
  `special_allowance` DECIMAL NOT NULL,
  `bonus` DECIMAL NOT NULL,
  `gross_earnings` DECIMAL NOT NULL,
  `provident_fund` DECIMAL NOT NULL,
  `professional_tax` DECIMAL NOT NULL,
  `tds` DECIMAL NOT NULL,
  `other_deductions` DECIMAL NOT NULL,
  `total_deductions` DECIMAL NOT NULL,
  `net_payable` DECIMAL NOT NULL,
  `status` VARCHAR(20) NOT NULL,
  `payment_date` DATE NULL,
  `payment_method` VARCHAR(50) NOT NULL,
  `transaction_ref` VARCHAR(100) NOT NULL,
  `generated_at` DATETIME(6) NULL NOT NULL,
  `employee_id` BIGINT NOT NULL,
  `payroll_period_id` BIGINT NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Dumping data for table `payroll_payslip` (2 records)
INSERT INTO `payroll_payslip` (`id`, `month`, `year`, `total_working_days`, `present_days`, `paid_leaves`, `loss_of_pay_days`, `payable_days`, `basic_salary`, `hra`, `conveyance_allowance`, `medical_allowance`, `special_allowance`, `bonus`, `gross_earnings`, `provident_fund`, `professional_tax`, `tds`, `other_deductions`, `total_deductions`, `net_payable`, `status`, `payment_date`, `payment_method`, `transaction_ref`, `generated_at`, `employee_id`, `payroll_period_id`) VALUES
  (1, 10, 2026, 26, 24, 2, 0, 26, 60000, 30000, 5000, 5000, 20000, 10000, 130000, 7200, 200, 8500, 0, 15900, 114100, 'APPROVED', '2026-10-31', 'DIRECT_BANK_TRANSFER', 'NEFT-HDFC-9928172635', '2026-11-01 15:07:14.669220', 4, 1),
  (2, 10, 2026, 26, 25, 1, 0, 26, 47500, 23750, 4000, 4000, 15750, 0, 95000, 5700, 200, 5500, 0, 11400, 83600, 'APPROVED', '2026-10-31', 'DIRECT_BANK_TRANSFER', 'NEFT-AXIS-8827163542', '2026-11-01 15:07:14.679139', 5, 1);


DROP TABLE IF EXISTS `performance_employeeaward`;
CREATE TABLE `performance_employeeaward` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `award_title` VARCHAR(150) NOT NULL,
  `month_year` VARCHAR(50) NOT NULL,
  `citation` LONGTEXT NOT NULL,
  `is_featured` TINYINT(1) NOT NULL,
  `created_at` DATETIME(6) NULL NOT NULL,
  `awarded_by_id` BIGINT,
  `employee_id` BIGINT NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Dumping data for table `performance_employeeaward` (2 records)
INSERT INTO `performance_employeeaward` (`id`, `award_title`, `month_year`, `citation`, `is_featured`, `created_at`, `awarded_by_id`, `employee_id`) VALUES
  (1, 'Employee of the Month', 'October 2026', 'Exceptional leadership in architecting and delivering the High-Performance Core API Module ahead of schedule with zero defect leakage.', 1, '2026-11-01 15:07:14.600662', 1, 4),
  (2, 'Quality Champion Award', 'September 2026', 'Pioneered an end-to-end automated testing regression pipeline that reduced deployment release cycles by 40%.', 1, '2026-11-01 15:07:14.609614', 3, 6);


DROP TABLE IF EXISTS `performance_goal`;
CREATE TABLE `performance_goal` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `title` VARCHAR(200) NOT NULL,
  `description` LONGTEXT NOT NULL,
  `target_date` DATE NULL NOT NULL,
  `status` VARCHAR(20) NOT NULL,
  `progress_percentage` BIGINT NOT NULL,
  `created_at` DATETIME(6) NULL NOT NULL,
  `updated_at` DATETIME(6) NULL NOT NULL,
  `assigned_by_id` BIGINT,
  `employee_id` BIGINT NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Dumping data for table `performance_goal` (2 records)
INSERT INTO `performance_goal` (`id`, `title`, `description`, `target_date`, `status`, `progress_percentage`, `created_at`, `updated_at`, `assigned_by_id`, `employee_id`) VALUES
  (1, 'Implement Microservices Event Bus Architecture', 'Refactor monolithic order communication pipeline to asynchronous event-driven architecture using Celery and Redis.', '2026-12-15', 'IN_PROGRESS', 75, '2026-11-01 15:07:14.783317', '2026-11-01 15:07:14.783444', 3, 4),
  (2, 'Mentor Junior Developers in Django ORM Optimization', 'Conduct bi-weekly code review workshops on query reduction, select_related, and indexing strategies.', '2026-11-30', 'IN_PROGRESS', 60, '2026-11-01 15:07:14.791324', '2026-11-01 17:08:49.567331', 3, 4);


DROP TABLE IF EXISTS `performance_performancereview`;
CREATE TABLE `performance_performancereview` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `review_cycle` VARCHAR(50) NOT NULL,
  `rating` BIGINT NOT NULL,
  `strengths` LONGTEXT NOT NULL,
  `areas_for_improvement` LONGTEXT NOT NULL,
  `manager_remarks` LONGTEXT NOT NULL,
  `employee_feedback` LONGTEXT NOT NULL,
  `recommendation` VARCHAR(30) NOT NULL,
  `status` VARCHAR(20) NOT NULL,
  `created_at` DATETIME(6) NULL NOT NULL,
  `updated_at` DATETIME(6) NULL NOT NULL,
  `employee_id` BIGINT NOT NULL,
  `reviewer_id` BIGINT,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Dumping data for table `performance_performancereview` (1 records)
INSERT INTO `performance_performancereview` (`id`, `review_cycle`, `rating`, `strengths`, `areas_for_improvement`, `manager_remarks`, `employee_feedback`, `recommendation`, `status`, `created_at`, `updated_at`, `employee_id`, `reviewer_id`) VALUES
  (1, 'Mid-Year Review 2026', 5, 'Exceptional problem-solving capabilities, proactive technical mentorship, and flawless production delivery.', 'Can delegate low-level routine bug fixes more effectively to focus on enterprise systems architecture.', 'Outstanding contributor. A cornerstone of the Engineering team.', '', 'PROMOTION', 'APPROVED', '2026-11-01 15:07:14.799187', '2026-11-01 15:07:14.799214', 4, 3);


DROP TABLE IF EXISTS `django_session`;
CREATE TABLE `django_session` (
  `session_key` VARCHAR(40) NOT NULL,
  `session_data` LONGTEXT NOT NULL,
  `expire_date` DATETIME(6) NULL NOT NULL,
  PRIMARY KEY (`session_key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Dumping data for table `django_session` (14 records)
INSERT INTO `django_session` (`session_key`, `session_data`, `expire_date`) VALUES
  ('ahx34gd3c0d3qhlcoba60dyotwe1yzt6', '.eJxVjE0OwiAYBe_C2hAolIBL956B8P0gVQNJaVeNd7dNutDtm5m3iZjWpcS18xwnElcxiMvvBglfXA9Az1QfTWKryzyBPBR50i7vjfh9O92_g5J62WvwgAqdQmMso9ZeGw0KwQ8uq0SUA2dgQ3ockQGCtWRzCor2zJJx4vMFBIY5Ag:1xNvKj:NSJZmkHYM9xHrbcMjiBj1Sof1lx96-MuGPE49qaAUWA', '2026-11-03 16:56:33.116274'),
  ('5553t1461ndhz9r13pq9i8exuazxnrxr', '.eJxVjE0OwiAYBe_C2hAolIBL956B8P0gVQNJaVeNd7dNutDtm5m3iZjWpcS18xwnElcxiMvvBglfXA9Az1QfTWKryzyBPBR50i7vjfh9O92_g5J62WvwgAqdQmMso9ZeGw0KwQ8uq0SUA2dgQ3ockQGCtWRzCor2zJJx4vMFBIY5Ag:1xNvYI:u-32DuHYymwISEgb7xDjr9KBhWLKpo_eKSGuoKXKoVs', '2026-11-03 17:10:34.249855'),
  ('tgw4y2ym053lo2g424tzckkhbitc781m', '.eJxVjE0OwiAYBe_C2hAolIBL956B8P0gVQNJaVeNd7dNutDtm5m3iZjWpcS18xwnElcxiMvvBglfXA9Az1QfTWKryzyBPBR50i7vjfh9O92_g5J62WvwgAqdQmMso9ZeGw0KwQ8uq0SUA2dgQ3ockQGCtWRzCor2zJJx4vMFBIY5Ag:1xNvgw:YPrBSgEIHZ1WZ9e8JkItEhb_5aoX07K3lofYurptDmI', '2026-11-03 17:19:30.832695'),
  ('8izmv9hdfm2qvxc5ggy7ym6ytx9qd3un', '.eJxVjE0OwiAYBe_C2hAolIBL956B8P0gVQNJaVeNd7dNutDtm5m3iZjWpcS18xwnElcxiMvvBglfXA9Az1QfTWKryzyBPBR50i7vjfh9O92_g5J62WvwgAqdQmMso9ZeGw0KwQ8uq0SUA2dgQ3ockQGCtWRzCor2zJJx4vMFBIY5Ag:1xNvmr:IEXb0bC-geKDeJjb8X3AM6mxqZMpLY60tyroskNLU14', '2026-11-03 17:25:37.019056'),
  ('n6kznbduphrbmw9ccru7i4b097a77a3s', '.eJxVjE0OwiAYBe_C2hAolIBL956B8P0gVQNJaVeNd7dNutDtm5m3iZjWpcS18xwnElcxiMvvBglfXA9Az1QfTWKryzyBPBR50i7vjfh9O92_g5J62WvwgAqdQmMso9ZeGw0KwQ8uq0SUA2dgQ3ockQGCtWRzCor2zJJx4vMFBIY5Ag:1xNvtz:Eqc6AAbw3g39WY9j7XjseZqYGQclyKij4fI4STofRqg', '2026-11-03 17:32:59.487526'),
  ('k42z8df7e6alkbqn8vl4723w4tiv1s6f', '.eJxVjEEOwiAQRe_C2hCYSnFcuvcMZBgGqRpISrsy3l2bdKHb_977LxVoXUpYu8xhSuqsQB1-t0j8kLqBdKd6a5pbXeYp6k3RO-362pI8L7v7d1Col29tB08jsj9myggQxQCnCMnZU0aK4AcymB1jyuJwsATIktnCSGzIgXp_APZFOIk:1xO7W2:4Xt9t2edUDMmEQt-tns9GA7rx9K4BsyjbCVsrNa91yw', '2026-11-04 05:57:02.334512'),
  ('wdzl98n6n1w9xdd2xbr043c12lntvqa6', '.eJxVjEEOwiAQRe_C2hCYSnFcuvcMZBgGqRpISrsy3l2bdKHb_977LxVoXUpYu8xhSuqsQB1-t0j8kLqBdKd6a5pbXeYp6k3RO-362pI8L7v7d1Col29tB08jsj9myggQxQCnCMnZU0aK4AcymB1jyuJwsATIktnCSGzIgXp_APZFOIk:1xO7Xh:3xAi-EnDfOmBmxwWOc9znbIKaPz4zGH-qfenfQhU8j4', '2026-11-04 05:58:45.683000'),
  ('pyhdxgjit6c2blns9ghq3d1hkwjyvq0f', '.eJxVjEEOwiAQRe_C2hCYSnFcuvcMZBgGqRpISrsy3l2bdKHb_977LxVoXUpYu8xhSuqsQB1-t0j8kLqBdKd6a5pbXeYp6k3RO-362pI8L7v7d1Col29tB08jsj9myggQxQCnCMnZU0aK4AcymB1jyuJwsATIktnCSGzIgXp_APZFOIk:1xO7cL:T6mrz_kV4HmyFKes5zHuFuvHfngzNH9vmIOdRtOo_vk', '2026-11-04 06:03:33.255600'),
  ('rsmug9e38an2rsq9yblqvyaygf6udio5', '.eJxVjEEOwiAQRe_C2hCYSnFcuvcMZBgGqRpISrsy3l2bdKHb_977LxVoXUpYu8xhSuqsQB1-t0j8kLqBdKd6a5pbXeYp6k3RO-362pI8L7v7d1Col29tB08jsj9myggQxQCnCMnZU0aK4AcymB1jyuJwsATIktnCSGzIgXp_APZFOIk:1xO7cW:0AdvrPt2ttNljkVtMIxGFJf840KEQX25CKyYqKRHTVA', '2026-11-04 06:03:44.402615'),
  ('xad34488brehw1d3k0tkok0coy5pubfh', '.eJxVjDsOwjAUBO_iGlnGcX6U9DmDtbb34QBKpDipEHeHSCmg3ZnZl_LY1uy3wsWPSV3UWZ1-t4D44LSDdMd0m3Wcp3UZg94VfdCihznxeT3cv4OMkr-1pWFlpe2NQNqYHK2t0CACBiYmBisWznUSKhKk1M7RpRpNF3uhen8AG-450Q:1xO7kU:89_jdgV7g_avO6UbyUDuJsBe9mJKTcVo4NcORFEploM', '2026-11-04 06:11:58.689190'),
  ('jlm8jtald24lbawsnl4gqcgb8ch2fun7', '.eJxVjEEOwiAQRe_C2hCYSnFcuvcMZBgGqRpISrsy3l2bdKHb_977LxVoXUpYu8xhSuqsQB1-t0j8kLqBdKd6a5pbXeYp6k3RO-362pI8L7v7d1Col29tB08jsj9myggQxQCnCMnZU0aK4AcymB1jyuJwsATIktnCSGzIgXp_APZFOIk:1xO7tO:662k8kC077lxWvnfB6QZCyvh7WAZnuiUqGm_w0vsSw4', '2026-11-04 06:21:10.840756'),
  ('1h8gt0gpyfyvxa504idjt0ttks8k57b4', '.eJxVjEEOwiAQRe_C2hCYSnFcuvcMZBgGqRpISrsy3l2bdKHb_977LxVoXUpYu8xhSuqsQB1-t0j8kLqBdKd6a5pbXeYp6k3RO-362pI8L7v7d1Col29tB08jsj9myggQxQCnCMnZU0aK4AcymB1jyuJwsATIktnCSGzIgXp_APZFOIk:1xO7tj:jcm2b_Cu98qnSwEkTfl9mEHx2XKI1K9GsKS7p0LnBv8', '2026-11-04 06:21:31.866152'),
  ('r279y1w0d5rkf5by7fuku7dmxbk1q2fo', '.eJxVjMsOwiAQRf-FtSE8CgWX7v0GMswMUjU0Ke3K-O_apAvd3nPOfYkE21rT1nlJE4mzMOL0u2XAB7cd0B3abZY4t3WZstwVedAurzPx83K4fwcVev3W1meHgNkqZSKFCOyYSWvv1OA1g1ZsnB1VwYLMnkMINlKEYM1YBs7i_QHsNzg2:1xOZ11:cFkATPKCWVqY2CF6ZaleZzJZzxcg9kFwVzs-FrIzDPc', '2026-11-05 11:18:51.187275'),
  ('qxhks2r55unf8ova2pfdtcykn9v05a8z', '.eJxVjDsOwjAQBe_iGln-beKlpM8ZLH82OIBsKU4qxN1xpBTQzsx7b-b8vmW3N1rdktiVKXb5ZcHHJ5VDpIcv98pjLdu6BH4k_LSNTzXR63a2fwfZt9zXxhDCKCMhWhFtmgGFxhGkGABQkR4IPdkE2D-V8RG1BDOHzrWIhtjnC8REN2E:1xOtUf:xE1-hg6nyB51ZlBIiTE0QdMEIqwOlEpxd-E7ZH68FH4', '2026-11-06 09:10:49.785603');


DROP TABLE IF EXISTS `support_asset`;
CREATE TABLE `support_asset` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `asset_tag` VARCHAR(50) NOT NULL,
  `name` VARCHAR(150) NOT NULL,
  `asset_type` VARCHAR(20) NOT NULL,
  `serial_number` VARCHAR(100) NOT NULL,
  `assigned_date` DATE NULL,
  `status` VARCHAR(20) NOT NULL,
  `specifications` LONGTEXT NOT NULL,
  `created_at` DATETIME(6) NULL NOT NULL,
  `assigned_to_id` BIGINT,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Dumping data for table `support_asset` (3 records)
INSERT INTO `support_asset` (`id`, `asset_tag`, `name`, `asset_type`, `serial_number`, `assigned_date`, `status`, `specifications`, `created_at`, `assigned_to_id`) VALUES
  (1, 'AST-BLR-0101', 'MacBook Pro 16" M3 Max (36GB RAM / 1TB SSD)', 'LAPTOP', 'C02G8712MD6R', '2022-04-11', 'ASSIGNED', 'Apple M3 Max 14-core CPU, 30-core GPU, 36GB Unified Memory, Space Black', '2026-11-01 15:07:14.834558', 4),
  (2, 'AST-BLR-0102', 'Dell UltraSharp 27" 4K USB-C Hub Monitor', 'MONITOR', 'CN-0N374M-74261', '2022-04-15', 'ASSIGNED', '', '2026-11-01 15:07:14.843431', 4),
  (3, 'AST-BLR-0205', 'ThinkPad P16s Gen 2 AMD Ryzen 7 PRO', 'LAPTOP', 'PF430291', NULL, 'AVAILABLE', 'Ryzen 7 PRO 7840U, 32GB LPDDR5x, 1TB NVMe Gen4', '2026-11-01 15:07:14.850855', NULL);


DROP TABLE IF EXISTS `support_officialdocumentrequest`;
CREATE TABLE `support_officialdocumentrequest` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `document_type` VARCHAR(30) NOT NULL,
  `purpose` LONGTEXT NOT NULL,
  `status` VARCHAR(20) NOT NULL,
  `issued_document` VARCHAR(100),
  `hr_remarks` LONGTEXT NOT NULL,
  `requested_at` DATETIME(6) NULL NOT NULL,
  `resolved_at` DATETIME(6) NULL,
  `employee_id` BIGINT NOT NULL,
  `reviewed_by_id` BIGINT,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Dumping data for table `support_officialdocumentrequest` (2 records)
INSERT INTO `support_officialdocumentrequest` (`id`, `document_type`, `purpose`, `status`, `issued_document`, `hr_remarks`, `requested_at`, `resolved_at`, `employee_id`, `reviewed_by_id`) VALUES
  (1, 'EMPLOYMENT_CERTIFICATE', 'Required for housing loan documentation submission to HDFC Bank.', 'PENDING', '', '', '2026-11-01 15:07:14.816747', NULL, 4, NULL),
  (2, 'EXPERIENCE_LETTER', 'Visa and passport renewal verification.', 'ISSUED', '', 'Certificate generated and countersigned.', '2026-11-01 15:07:14.825208', '2026-10-27 15:07:14.823421', 5, 2);


DROP TABLE IF EXISTS `support_supportticket`;
CREATE TABLE `support_supportticket` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `category` VARCHAR(20) NOT NULL,
  `priority` VARCHAR(10) NOT NULL,
  `subject` VARCHAR(200) NOT NULL,
  `description` LONGTEXT NOT NULL,
  `attachment` VARCHAR(100),
  `status` VARCHAR(20) NOT NULL,
  `resolution_notes` LONGTEXT NOT NULL,
  `created_at` DATETIME(6) NULL NOT NULL,
  `resolved_at` DATETIME(6) NULL,
  `assigned_to_id` BIGINT,
  `employee_id` BIGINT NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Dumping data for table `support_supportticket` (2 records)
INSERT INTO `support_supportticket` (`id`, `category`, `priority`, `subject`, `description`, `attachment`, `status`, `resolution_notes`, `created_at`, `resolved_at`, `assigned_to_id`, `employee_id`) VALUES
  (1, 'IT_SUPPORT', 'MEDIUM', 'Additional 32-inch 4K Monitor Request for Multi-Display Setup', 'Requesting secondary high-resolution display for backend microservices profiling and monitoring dashboards.', '', 'RESOLVED', '', '2026-11-01 15:07:14.807033', '2026-11-04 07:29:00.404709', 1, 4),
  (2, 'IT_SUPPORT', 'MEDIUM', 'information', 'provide it', 'ticket_attachments/5cd24bbd-4dd1-4a25-b3c9-83e3dd5ed9a3.png', 'OPEN', '', '2026-11-04 07:30:33.968086', NULL, NULL, 4);


DROP TABLE IF EXISTS `support_ticketcomment`;
CREATE TABLE `support_ticketcomment` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `comment` LONGTEXT NOT NULL,
  `created_at` DATETIME(6) NULL NOT NULL,
  `ticket_id` BIGINT NOT NULL,
  `user_id` BIGINT NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Dumping data for table `support_ticketcomment` (1 records)
INSERT INTO `support_ticketcomment` (`id`, `comment`, `created_at`, `ticket_id`, `user_id`) VALUES
  (1, 'some time wait plese', '2026-11-04 07:29:00.397229', 1, 2);


DROP TABLE IF EXISTS `recruitment_candidatedocument`;
CREATE TABLE `recruitment_candidatedocument` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `doc_type` VARCHAR(30) NOT NULL,
  `title` VARCHAR(200) NOT NULL,
  `file` VARCHAR(100) NOT NULL,
  `uploaded_at` DATETIME(6) NULL NOT NULL,
  `candidate_id` BIGINT NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS `recruitment_candidateexperience`;
CREATE TABLE `recruitment_candidateexperience` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `experience_type` VARCHAR(20) NOT NULL,
  `total_experience_years` BIGINT NOT NULL,
  `total_experience_months` BIGINT NOT NULL,
  `current_company` VARCHAR(150) NOT NULL,
  `current_designation` VARCHAR(150) NOT NULL,
  `previous_company` VARCHAR(150) NOT NULL,
  `previous_experience_details` LONGTEXT NOT NULL,
  `current_ctc` DECIMAL,
  `expected_ctc` DECIMAL,
  `notice_period_days` BIGINT NOT NULL,
  `available_joining_date` DATE NULL,
  `candidate_id` BIGINT NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Dumping data for table `recruitment_candidateexperience` (5 records)
INSERT INTO `recruitment_candidateexperience` (`id`, `experience_type`, `total_experience_years`, `total_experience_months`, `current_company`, `current_designation`, `previous_company`, `previous_experience_details`, `current_ctc`, `expected_ctc`, `notice_period_days`, `available_joining_date`, `candidate_id`) VALUES
  (5, 'FRESHER', 0, 0, '', '', '', '', NULL, 80000000, 30, NULL, 5),
  (6, 'EXPERIENCED', 6, 2, 'Infosys Limited (Bhubaneswar SEZ)', 'Senior Technology Specialist', 'Mindtree Consulting', 'Full-stack development of financial billing portals using Django, PostgreSQL, and Angular.', 1500000, 2200000, 30, '2026-12-15', 6),
  (7, 'EXPERIENCED', 5, 6, 'Swiggy', 'Senior Product Designer', 'Razorpay', 'Led design for merchant analytics dashboards, checkout flow optimizations, and design system tokens.', 1900000, 2600000, 45, '2026-12-25', 7),
  (8, 'FRESHER', 0, 0, '', '', '', '', NULL, 550000, 0, '2026-11-20', 8),
  (9, 'EXPERIENCED', 3, 4, 'Tata Consultancy Services (TCS Bhubaneswar)', 'Systems Engineer (Python Developer)', '', 'Developed RESTful services with Django REST framework and integrated third-party payment gateways.', 900000, 1400000, 60, '2027-01-09', 9);


DROP TABLE IF EXISTS `recruitment_candidateskill`;
CREATE TABLE `recruitment_candidateskill` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `technical_skills` LONGTEXT NOT NULL,
  `programming_languages` VARCHAR(255) NOT NULL,
  `frameworks` VARCHAR(255) NOT NULL,
  `certifications` LONGTEXT NOT NULL,
  `projects` LONGTEXT NOT NULL,
  `preferred_role` VARCHAR(150) NOT NULL,
  `preferred_location` VARCHAR(150) NOT NULL,
  `portfolio_url` VARCHAR(200) NOT NULL,
  `linkedin_url` VARCHAR(200) NOT NULL,
  `github_url` VARCHAR(200) NOT NULL,
  `candidate_id` BIGINT NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Dumping data for table `recruitment_candidateskill` (5 records)
INSERT INTO `recruitment_candidateskill` (`id`, `technical_skills`, `programming_languages`, `frameworks`, `certifications`, `projects`, `preferred_role`, `preferred_location`, `portfolio_url`, `linkedin_url`, `github_url`, `candidate_id`) VALUES
  (5, 'python,java', '', '', '', '', '', '', 'http://127.0.0.1:8000/candidate/register/15AVn0thgXNvIbeDieD7lA/', 'http://127.0.0.1:8000/candidate/register/15AVn0thgXNvIbeDieD7lA/', '', 5),
  (6, 'Python 3, Django, Django REST Framework, PostgreSQL, Redis, Celery, Docker, Linux, Git, Unit Testing', 'Python, JavaScript, SQL, Bash', 'Django, FastAPI, Bootstrap 5, Tailwind CSS', 'AWS Solutions Architect Associate, Python Certified Professional', 'High-throughput enterprise HRMS API gateway handling 100k daily requests with sub-100ms response time.', 'Senior Full-Stack Django Developer', 'Bhubaneswar / Bengaluru', 'https://priyabratanayak.dev', 'https://linkedin.com/in/priyabrata-nayak-sample', 'https://github.com/priyabratanayak-sample', 6),
  (7, 'Figma, Design Systems, Wireframing, High-fidelity Prototyping, Usability Testing, User Journey Mapping, Design Tokens', 'HTML5, CSS3, Basic React', 'Tailwind CSS, Bootstrap, Material 3', 'NN/g UX Master Certification, Interaction Design Foundation', 'Revamped merchant analytics portal resulting in 34% increase in dashboard engagement and 18% reduction in support tickets.', 'Lead UI/UX Product Designer', 'Bhubaneswar / Bengaluru', 'https://chinmayeedesigns.work', 'https://linkedin.com/in/chinmayee-mohanty-sample', '', 7),
  (8, 'Python, Django, SQLite, PostgreSQL, HTML5, CSS3, JavaScript, Git, Linux', 'Python, C++, SQL', 'Django, Bootstrap 5', 'Python for Everybody Specialization (Coursera)', 'Built student attendance & library management system with Django and role-based permissions.', 'Graduate Trainee / Junior Python Developer', 'Bhubaneswar / Bengaluru', 'https://github.com/tapasbehera-sample', 'https://linkedin.com/in/tapas-behera-sample', 'https://github.com/tapasbehera-sample', 8),
  (9, 'Python, Django REST Framework, MySQL, Git, Postman, Jenkins', 'Python, SQL', 'Django, DRF', 'Oracle Certified Associate Python', 'Automated reporting pipeline for retail analytics client.', 'Python Developer', 'Bhubaneswar', '', 'https://linkedin.com/in/lipsa-pradhan-sample', 'https://github.com/lipsapradhan-sample', 9);


DROP TABLE IF EXISTS `recruitment_applicationstatushistory`;
CREATE TABLE `recruitment_applicationstatushistory` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `old_status` VARCHAR(30) NOT NULL,
  `new_status` VARCHAR(30) NOT NULL,
  `notes` LONGTEXT NOT NULL,
  `changed_at` DATETIME(6) NULL NOT NULL,
  `changed_by_id` BIGINT,
  `application_id` BIGINT NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Dumping data for table `recruitment_applicationstatushistory` (30 records)
INSERT INTO `recruitment_applicationstatushistory` (`id`, `old_status`, `new_status`, `notes`, `changed_at`, `changed_by_id`, `application_id`) VALUES
  (9, 'NONE', 'SUBMITTED', 'Application submitted online for Round 1 Interview Screening.', '2026-11-02 12:04:43.206902', NULL, 5),
  (10, 'INTERVIEW_SCHEDULED', 'INTERVIEW_SCHEDULED', 'Interview scheduled on 2026-11-26 at 22:38:00 (In-Person (Office Campus))', '2026-11-02 12:08:28.423658', 2, 5),
  (11, 'INTERVIEW_SCHEDULED', 'INTERVIEW_SCHEDULED', 'Interview scheduled on 2026-11-02 at 17:52:00 (Virtual (Google Meet / Microsoft Teams))', '2026-11-02 12:20:08.277235', 2, 5),
  (12, 'INTERVIEW_SCHEDULED', 'SHORTLISTED', 'good ', '2026-11-02 12:22:02.174166', 1, 5),
  (13, 'SHORTLISTED', 'HIRED', '', '2026-11-02 12:25:45.146123', 2, 5),
  (14, 'HIRED', 'ONBOARDING_COMPLETED', 'Full onboarding particulars and verification documents submitted by qualified candidate.', '2026-11-02 12:29:52.987195', NULL, 5),
  (15, 'HIRED', 'HIRED', 'Candidate successfully converted to Company Employee (slipu061). Employee Profile #EMP112 created.', '2026-11-02 12:30:58.504845', 2, 5),
  (16, 'INTERVIEW_SCHEDULED', 'INTERVIEW_SCHEDULED', 'Interview scheduled on 2026-11-02 at 17:52:00 (Virtual (Google Meet / Microsoft Teams))', '2026-11-02 12:58:14.187124', 2, 5),
  (17, 'INTERVIEW_SCHEDULED', 'HIRED', '', '2026-11-02 12:58:28.419218', 2, 5),
  (18, 'HIRED', 'ONBOARDING_COMPLETED', 'Full onboarding particulars and verification documents submitted by qualified candidate.', '2026-11-02 12:59:33.160013', NULL, 5),
  (19, 'HIRED', 'HIRED', 'Candidate successfully converted to Company Employee (slipu061). Employee Profile #EMP112 created.', '2026-11-02 13:01:50.379913', 1, 5),
  (20, 'HIRED', 'ONBOARDING_COMPLETED', '', '2026-11-02 13:08:09.879285', 2, 5),
  (21, 'HIRED', 'HIRED', 'Candidate successfully converted to Company Employee (slipu061). Employee Profile #EMP112 created.', '2026-11-02 13:08:51.749747', 2, 5),
  (22, 'HIRED', 'ONBOARDING_COMPLETED', '', '2026-11-02 13:18:18.824631', 1, 5),
  (23, 'ONBOARDING_COMPLETED', 'HIRED', '', '2026-11-02 13:18:32.476636', 1, 5),
  (24, 'HIRED', 'ONBOARDING_COMPLETED', '', '2026-11-02 13:18:49.289819', 1, 5),
  (25, 'HIRED', 'HIRED', 'Candidate successfully converted to Company Employee (slipu061). Employee Profile #EMP112 created.', '2026-11-02 13:18:56.747990', 1, 5),
  (27, 'NONE', 'SUBMITTED', 'Application submitted via online portal for Round 1 Interview Screening.', '2026-11-03 10:17:00.646570', NULL, 6),
  (28, 'SUBMITTED', 'REJECTED', '', '2026-11-04 06:04:37.737482', 2, 6),
  (29, 'REJECTED', 'HIRED', '', '2026-11-04 06:09:06.987816', 2, 6),
  (30, 'HIRED', 'REJECTED', '', '2026-11-04 06:19:28.426834', 2, 6),
  (31, 'REJECTED', 'HIRED', '', '2026-11-04 06:20:03.623849', 2, 6),
  (32, 'NONE', 'SUBMITTED', 'Application received via LinkedIn Campaign link.', '2026-11-05 02:15:38.337845', NULL, 7),
  (33, 'SUBMITTED', 'SHORTLISTED', 'Shortlisted based on 6 years relevant experience and NIT Rourkela background.', '2026-11-05 02:15:38.342800', 2, 7),
  (34, 'SHORTLISTED', 'INTERVIEW_SCHEDULED', 'Virtual Technical Round 2 scheduled for 2:30 PM with VP of Engineering.', '2026-11-05 02:15:38.347430', 2, 7),
  (35, 'NONE', 'SUBMITTED', 'Application received via Dribbble & Design link.', '2026-11-05 02:15:38.393549', NULL, 8),
  (36, 'SUBMITTED', 'SHORTLISTED', 'Shortlisted based on NID credentials and Razorpay/Swiggy product portfolio.', '2026-11-05 02:15:38.398312', 2, 8),
  (37, 'NONE', 'SUBMITTED', 'Application received via Campus Drive link.', '2026-11-05 02:15:38.443180', NULL, 9),
  (38, 'SUBMITTED', 'UNDER_REVIEW', 'Profile queued for screening test evaluation.', '2026-11-05 02:15:38.447698', 2, 9),
  (39, 'NONE', 'SUBMITTED', 'Application received via WhatsApp & Referral channel.', '2026-11-05 02:15:38.492675', NULL, 10);


DROP TABLE IF EXISTS `recruitment_recruitmentjob`;
CREATE TABLE `recruitment_recruitmentjob` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `title` VARCHAR(200) NOT NULL,
  `location` VARCHAR(150) NOT NULL,
  `employment_type` VARCHAR(20) NOT NULL,
  `vacancies` BIGINT NOT NULL,
  `experience_required` VARCHAR(50) NOT NULL,
  `salary_range` VARCHAR(100) NOT NULL,
  `description` LONGTEXT NOT NULL,
  `requirements` LONGTEXT NOT NULL,
  `benefits` LONGTEXT NOT NULL,
  `application_deadline` DATE NULL,
  `status` VARCHAR(20) NOT NULL,
  `created_at` DATETIME(6) NULL NOT NULL,
  `updated_at` DATETIME(6) NULL NOT NULL,
  `created_by_id` BIGINT,
  `department_id` BIGINT,
  `site_id` BIGINT,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Dumping data for table `recruitment_recruitmentjob` (5 records)
INSERT INTO `recruitment_recruitmentjob` (`id`, `title`, `location`, `employment_type`, `vacancies`, `experience_required`, `salary_range`, `description`, `requirements`, `benefits`, `application_deadline`, `status`, `created_at`, `updated_at`, `created_by_id`, `department_id`, `site_id`) VALUES
  (1, 'Senior Full-Stack Django Developer', 'Bengaluru HQ & Hybrid', 'FULL_TIME', 3, '4-8 Years', '₹18,00,000 - ₹28,00,000 PA', 'We are seeking an experienced Senior Full-Stack Django Developer to architect, develop, and scale enterprise web applications, real-time dashboards, and secure RBAC microservices. You will work closely with engineering leads and product managers to drive technical excellence.', '• Strong expertise in Python 3, Django, Django REST Framework, and ORM query optimization.
• Experience with PostgreSQL database tuning, Redis caching, and Celery task queues.
• Proficiency in modern frontend technologies: HTML5, CSS3/Tailwind/Bootstrap, JavaScript (ES6+).
• Familiarity with Docker containerization, CI/CD pipelines, and AWS cloud deployment.
• Bachelor\'s or Master\'s degree in Computer Science, Software Engineering, or equivalent.', '• Comprehensive medical insurance covering family & parents.
• Flexible hybrid work policy (2 days WFH / week).
• Annual performance bonus and learning & certification stipend.
• Ergonomic home office setup allowance.', '2026-12-07', 'OPEN', '2026-11-02 10:37:34.080872', '2026-11-02 12:10:56.904681', 2, 1, 1),
  (2, 'Lead UI/UX Product Designer', 'Bengaluru HQ (Hybrid)', 'FULL_TIME', 2, '5-9 Years', '₹20,00,000 - ₹30,00,000 PA', 'Lead the UI/UX design lifecycle for enterprise SaaS applications, internal portals, and design systems. Craft intuitive user workflows, interaction patterns, design tokens, and conduct user research.', '• Proven portfolio showcasing end-to-end B2B SaaS or enterprise web applications.
• Mastery of Figma, auto-layout, interactive prototypes, and design systems.
• Deep understanding of design accessibility (WCAG), responsive grids, and design tokens.
• Ability to translate complex domain workflows into elegant, friction-free interfaces.', '• Top-tier Apple MacBook Pro M3 Max hardware provided.
• Annual conference budget for Figma Config and UX design summits.
• Competitive health insurance and wellness perks.', '2026-12-17', 'OPEN', '2026-11-02 10:37:34.088302', '2026-11-02 10:37:34.088313', 2, 3, 1),
  (3, 'Graduate Trainee / Junior Python Engineer', 'Bengaluru HQ', 'INTERNSHIP', 5, 'Fresher / 0-1 Year', '₹4,50,000 - ₹6,50,000 PA', 'Fast-track your software engineering career with hands-on mentorship from senior architects. Participate in building core modules, automated testing suites, and backend APIs.', '• B.Tech / B.E. / MCA / B.Sc in Computer Science (2025/2026 batch) with minimum 70% or 7.0 CGPA.
• Solid foundation in Python programming, OOP principles, and relational databases (SQL).
• Passion for problem-solving, clean code, and fast-paced learning.', '• Paid 6-month internship with pre-placement full-time offer conversion.
• Free catered meals and daily office shuttle.', '2026-11-22', 'OPEN', '2026-11-02 10:37:34.092447', '2026-11-02 10:37:34.092459', 2, 1, 1),
  (4, 'architectures', 'Bengaluru HQ & Hybrid', 'FULL_TIME', 20, '2-5 Years', '', 'good and benificial data', 'autocad and more', '', NULL, 'OPEN', '2026-11-03 05:33:53.848595', '2026-11-03 09:32:06.505310', 2, NULL, NULL),
  (5, 'django developer', 'Hyderabad Innovation Campus (Hyderabad)', 'INTERNSHIP', 1, '2-5 Years', '', 'it is good and best', 'it is a remort job', '', NULL, 'OPEN', '2026-11-03 10:14:30.419009', '2026-11-03 10:14:30.419136', 2, 1, 2);


DROP TABLE IF EXISTS `recruitment_candidateregistrationlink`;
CREATE TABLE `recruitment_candidateregistrationlink` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `token` VARCHAR(64) NOT NULL,
  `title` VARCHAR(200) NOT NULL,
  `expires_at` DATETIME(6) NULL,
  `max_applications` BIGINT,
  `is_active` TINYINT(1) NOT NULL,
  `views_count` BIGINT NOT NULL,
  `created_at` DATETIME(6) NULL NOT NULL,
  `created_by_id` BIGINT,
  `job_id` BIGINT NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Dumping data for table `recruitment_candidateregistrationlink` (6 records)
INSERT INTO `recruitment_candidateregistrationlink` (`id`, `token`, `title`, `expires_at`, `max_applications`, `is_active`, `views_count`, `created_at`, `created_by_id`, `job_id`) VALUES
  (1, 'linkedin-sr-django-2026', 'LinkedIn Talent Solutions Q4 Campaign', '2026-12-02 10:37:34.096331', 100, 1, 142, '2026-11-02 10:37:34.097209', 2, 1),
  (2, 'referral-django-blr', 'WhatsApp & Employee Referral Channel', '2026-12-17 10:37:34.101318', 50, 0, 68, '2026-11-02 10:37:34.102058', 2, 1),
  (3, 'dribbble-uiux-lead-2026', 'Dribbble & Design Communities Portal', '2026-12-12 10:37:34.105524', 30, 1, 95, '2026-11-02 10:37:34.106297', 2, 2),
  (4, 'campus-freshers-2026', 'College Campus Drive 2026', '2026-11-17 10:37:34.109803', 150, 1, 310, '2026-11-02 10:37:34.110504', 2, 3),
  (5, 'expired-contractor-sample', 'Archived Contractor Drive (Closed)', '2026-10-28 10:37:34.114221', 10, 0, 22, '2026-11-02 10:37:34.115208', 2, 1),
  (6, '15AVn0thgXNvIbeDieD7lA', 'nbbb', '2026-11-03 11:38:00', 8, 1, 8, '2026-11-02 11:39:23.823910', 2, 1);


DROP TABLE IF EXISTS `recruitment_jobapplication`;
CREATE TABLE `recruitment_jobapplication` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `application_id` VARCHAR(30) NOT NULL,
  `resume` VARCHAR(100) NOT NULL,
  `status` VARCHAR(30) NOT NULL,
  `hr_notes` LONGTEXT NOT NULL,
  `rating` BIGINT NOT NULL,
  `interview_date` DATE NULL,
  `interview_time` TIME(6) NULL,
  `interview_mode` VARCHAR(30) NOT NULL,
  `interview_location_link` VARCHAR(255) NOT NULL,
  `interview_notes` LONGTEXT NOT NULL,
  `applied_at` DATETIME(6) NULL NOT NULL,
  `updated_at` DATETIME(6) NULL NOT NULL,
  `candidate_id` BIGINT NOT NULL,
  `registration_link_id` BIGINT,
  `job_id` BIGINT NOT NULL,
  `is_onboarding_completed` TINYINT(1) NOT NULL,
  `onboarding_completed_at` DATETIME(6) NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Dumping data for table `recruitment_jobapplication` (6 records)
INSERT INTO `recruitment_jobapplication` (`id`, `application_id`, `resume`, `status`, `hr_notes`, `rating`, `interview_date`, `interview_time`, `interview_mode`, `interview_location_link`, `interview_notes`, `applied_at`, `updated_at`, `candidate_id`, `registration_link_id`, `job_id`, `is_onboarding_completed`, `onboarding_completed_at`) VALUES
  (5, 'APP-10369', 'candidates/resumes/sip_report.docx', 'HIRED', 'good and benificial', 5, '2026-11-02', '17:52:00', 'VIRTUAL', 'http://127.0.0.1:8000/candidate/register/15AVn0thgXNvIbeDieD7lA/', 'dndndndnjdjdddjdnd', '2026-11-02 12:04:43.205799', '2026-11-02 17:37:12.376916', 5, 6, 1, 1, '2026-11-02 12:59:33.158029'),
  (6, 'APP-78277', 'candidates/resumes/sip_report_SKjtKfG.docx', 'HIRED', '', 0, NULL, NULL, 'VIRTUAL', '', '', '2026-11-03 10:17:00.644550', '2026-11-04 06:20:03.607437', 5, NULL, 5, 0, NULL),
  (7, 'APP-61355', 'candidates/resumes/Priyabrata_Nayak_Resume.pdf', 'INTERVIEW_SCHEDULED', 'Exceptional technical profile. Scored 95% on Django ORM optimization and Celery architectural screening. Demonstrated deep understanding of multi-tenant database design and security headers.', 5, '2026-11-08', '14:30:00', 'VIRTUAL', 'https://meet.google.com/abc-defg-hij', 'Round 2 Technical Deep Dive with VP of Engineering Debasish Mohapatra. Agenda: System design discussion, database query tuning exercise, and architecture walkthrough.', '2026-11-05 02:15:38.327199', '2026-11-05 02:15:38.332741', 6, 1, 1, 0, NULL),
  (8, 'APP-92349', 'candidates/resumes/Chinmayee_Mohanty_Resume.pdf', 'SHORTLISTED', 'World-class portfolio on enterprise design tokens and dashboard analytics. Highly articulate design rationale. Moving to portfolio presentation stage.', 4, NULL, NULL, 'VIRTUAL', '', '', '2026-11-05 02:15:38.383411', '2026-11-05 02:15:38.388413', 7, 3, 2, 0, NULL),
  (9, 'APP-10569', 'candidates/resumes/Tapas_Behera_Fresher_Resume.pdf', 'UNDER_REVIEW', 'Strong fresher profile with high CGPA and hands-on Django projects. Good potential for the engineering graduate cohort.', 4, NULL, NULL, 'VIRTUAL', '', '', '2026-11-05 02:15:38.433158', '2026-11-05 02:15:38.438355', 8, 4, 3, 0, NULL),
  (10, 'APP-84772', 'candidates/resumes/Lipsa_Pradhan_Resume.pdf', 'SUBMITTED', '', 0, NULL, NULL, 'VIRTUAL', '', '', '2026-11-05 02:15:38.483807', '2026-11-05 02:15:38.487979', 9, 2, 1, 0, NULL);


DROP TABLE IF EXISTS `recruitment_candidateeducation`;
CREATE TABLE `recruitment_candidateeducation` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `highest_qualification` VARCHAR(100) NOT NULL,
  `degree_name` VARCHAR(150) NOT NULL,
  `specialization` VARCHAR(150) NOT NULL,
  `institution` VARCHAR(200) NOT NULL,
  `percentage_cgpa` VARCHAR(20) NOT NULL,
  `details_10th` VARCHAR(150) NOT NULL,
  `details_12th` VARCHAR(150) NOT NULL,
  `additional_qualifications` LONGTEXT NOT NULL,
  `candidate_id` BIGINT NOT NULL,
  `passing_year` BIGINT,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Dumping data for table `recruitment_candidateeducation` (5 records)
INSERT INTO `recruitment_candidateeducation` (`id`, `highest_qualification`, `degree_name`, `specialization`, `institution`, `percentage_cgpa`, `details_10th`, `details_12th`, `additional_qualifications`, `candidate_id`, `passing_year`) VALUES
  (5, 'b.com', 'b.com', 'ai', 'giet', '98%', 'chse 2027-78', 'state bord 2021', '', 5, 2025),
  (6, 'B.Tech / B.E.', 'Bachelor of Technology in Computer Science & Engineering', 'Computer Science & Distributed Systems', 'National Institute of Technology (NIT) Rourkela', '8.7 CGPA', 'BSE Odisha Board - 94.2% (2012)', 'CHSE Odisha Board - 96.0% (2014)', 'Certified AWS Solutions Architect Associate (2024)', 6, 2018),
  (7, 'Bachelor of Design (B.Des)', 'B.Des in Interaction & Communication Design', 'Human-Computer Interaction (HCI)', 'National Institute of Design (NID) Ahmedabad', '8.9 CGPA', 'ICSE Board - 92.5%', 'ISC Board - 94.0%', 'Nielsen Norman Group UX Master Certified', 7, 2019),
  (8, 'B.Tech / B.E.', 'B.Tech in Computer Science & Engineering', 'Software Engineering', 'Odisha University of Technology and Research (OUTR), Bhubaneswar', '8.8 CGPA', 'BSE Odisha - 91.0%', 'CHSE Odisha - 93.5%', 'LeetCode 400+ problems solved, HackerRank 5-star Python', 8, 2025),
  (9, 'MCA (Master of Computer Applications)', 'Master of Computer Applications', 'Cloud Computing & Database Systems', 'Silicon Institute of Technology, Bhubaneswar', '8.4 CGPA', 'BSE Odisha Board - 89.0%', 'CHSE Odisha Board - 91.2%', '', 9, 2021);


DROP TABLE IF EXISTS `recruitment_candidate`;
CREATE TABLE `recruitment_candidate` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `full_name` VARCHAR(150) NOT NULL,
  `email` VARCHAR(254) NOT NULL,
  `phone` VARCHAR(20) NOT NULL,
  `alt_phone` VARCHAR(20) NOT NULL,
  `date_of_birth` DATE NULL,
  `gender` VARCHAR(20) NOT NULL,
  `photo` VARCHAR(100),
  `current_address` LONGTEXT NOT NULL,
  `city` VARCHAR(100) NOT NULL,
  `state` VARCHAR(100) NOT NULL,
  `postal_code` VARCHAR(20) NOT NULL,
  `country` VARCHAR(100) NOT NULL,
  `created_at` DATETIME(6) NULL NOT NULL,
  `aadhaar_number` VARCHAR(20) NOT NULL,
  `bank_account_number` VARCHAR(50) NOT NULL,
  `bank_branch` VARCHAR(150) NOT NULL,
  `bank_ifsc_code` VARCHAR(20) NOT NULL,
  `bank_name` VARCHAR(150) NOT NULL,
  `blood_group` VARCHAR(10) NOT NULL,
  `emergency_contact_name` VARCHAR(150) NOT NULL,
  `emergency_contact_phone` VARCHAR(20) NOT NULL,
  `emergency_contact_relation` VARCHAR(50) NOT NULL,
  `father_name` VARCHAR(150) NOT NULL,
  `marital_status` VARCHAR(20) NOT NULL,
  `pan_number` VARCHAR(20) NOT NULL,
  `permanent_address` LONGTEXT NOT NULL,
  `pf_uan_number` VARCHAR(30) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Dumping data for table `recruitment_candidate` (5 records)
INSERT INTO `recruitment_candidate` (`id`, `full_name`, `email`, `phone`, `alt_phone`, `date_of_birth`, `gender`, `photo`, `current_address`, `city`, `state`, `postal_code`, `country`, `created_at`, `aadhaar_number`, `bank_account_number`, `bank_branch`, `bank_ifsc_code`, `bank_name`, `blood_group`, `emergency_contact_name`, `emergency_contact_phone`, `emergency_contact_relation`, `father_name`, `marital_status`, `pan_number`, `permanent_address`, `pf_uan_number`) VALUES
  (5, 'arti sha', 'slipu061@gmail.com', '+913456787898', '', '2005-06-04', 'MALE', '', 'tyru', 'bhubaneswar', 'Odisha', '234566', 'India', '2026-11-02 12:04:43.177452', '97678547646', 'axcdsvfrc667775654545609', 'banglore', 'hdfc565465456654', 'hdfc', 'o+', '9876543212', '+913456787898', 'daughter', 'pice kumar', 'SINGLE', 'asfdc987898v', 'tyru', ''),
  (6, 'Priyabrata Nayak', 'priyabrata.nayak.dev@gmail.com', '+91 98610 43210', '+91 98610 43211', '1996-05-14', 'MALE', '', 'Plot 102, Saheed Nagar', 'Bhubaneswar', 'Odisha', '751007', 'India', '2026-11-05 02:15:38.291065', '', '', '', '', '', '', '', '', '', '', '', '', '', ''),
  (7, 'Chinmayee Mohanty', 'chinmayee.mohanty.ux@gmail.com', '+91 97781 32109', '', '1997-08-22', 'FEMALE', '', 'Flat 204, Jayadev Vihar', 'Bhubaneswar', 'Odisha', '751013', 'India', '2026-11-05 02:15:38.353776', '', '', '', '', '', '', '', '', '', '', '', '', '', ''),
  (8, 'Tapas Kumar Behera', 'tapas.behera.2025@gmail.com', '+91 94371 21098', '', '2003-11-08', 'MALE', '', 'Room 304, Boys Hostel 2, OUTR Campus, Ghatikia', 'Bhubaneswar', 'Odisha', '751003', 'India', '2026-11-05 02:15:38.404120', '', '', '', '', '', '', '', '', '', '', '', '', '', ''),
  (9, 'Lipsa Pradhan', 'lipsa.pradhan.backend@gmail.com', '+91 99370 10987', '', '1998-03-19', 'FEMALE', '', 'Quarter 12, CDA Sector 9', 'Cuttack', 'Odisha', '753014', 'India', '2026-11-05 02:15:38.454131', '', '', '', '', '', '', '', '', '', '', '', '', '', '');


SET FOREIGN_KEY_CHECKS = 1;
-- Export completed successfully.
