-- =====================================================
-- QUESTION BANK TABLES
-- =====================================================

CREATE TABLE tbl_cp_mquestions (
  row_id        INT NOT NULL IDENTITY(1,1) PRIMARY KEY,
  question_id   INT NOT NULL UNIQUE,
  module_id     INT NOT NULL,
  difficulty_id INT NOT NULL,
  question_text TEXT NOT NULL,
  question_type VARCHAR(50) NOT NULL DEFAULT 'mcq',
  correct_answer TEXT,
  max_marks     DECIMAL(6,2) NOT NULL DEFAULT 1.0,
  is_active     BIT NULL,
  created_at    DATETIME2 DEFAULT GETUTCDATE(),
  updated_at    DATETIME2 DEFAULT GETUTCDATE(),
  FOREIGN KEY (module_id)     REFERENCES tbl_cp_mmodule(module_id) ON DELETE NO ACTION,
  FOREIGN KEY (difficulty_id) REFERENCES tbl_cp_mdifficulty(difficulty_id) ON DELETE NO ACTION
);

CREATE TABLE tbl_cp_m2m_question_options (
  row_id        INT NOT NULL IDENTITY(1,1) PRIMARY KEY,
  option_id     INT NOT NULL UNIQUE,
  question_id   INT NOT NULL,
  option_text   TEXT NOT NULL,
  is_correct    BIT NULL,
  display_order INT NOT NULL DEFAULT 1,
  created_at    DATETIME2 DEFAULT GETUTCDATE(),
  updated_at    DATETIME2 DEFAULT GETUTCDATE(),
  FOREIGN KEY (question_id) REFERENCES tbl_cp_mquestions(question_id) ON DELETE NO ACTION
);

-- =====================================================
-- COMPANY & JOB DESCRIPTION TABLES
-- =====================================================

CREATE TABLE tbl_cp_mcompany (
  row_id     INT NOT NULL IDENTITY(1,1) PRIMARY KEY,
  company_id INT NOT NULL UNIQUE,
  name       VARCHAR(255) NOT NULL UNIQUE,
  industry   VARCHAR(150) DEFAULT 'Not Specified',
  website    VARCHAR(255) DEFAULT '',
  city       VARCHAR(100) DEFAULT 'Not Specified',
  is_active  BIT NULL,
  created_at DATETIME2 DEFAULT GETUTCDATE(),
  updated_at DATETIME2 DEFAULT GETUTCDATE()
);

CREATE TABLE tbl_cp_job_description (
  row_id               INT NOT NULL IDENTITY(1,1) PRIMARY KEY,
  jd_id                INT NOT NULL UNIQUE,
  company_id           INT NOT NULL,
  job_role             VARCHAR(150) NOT NULL DEFAULT 'Not Specified',
  title                VARCHAR(255) NOT NULL,
  description          TEXT,
  experience_min_yrs   DECIMAL(4,1) DEFAULT 0.0,
  experience_max_yrs   DECIMAL(4,1) DEFAULT 0.0,
  salary_min           DECIMAL(12,2) DEFAULT 0.00,
  salary_max           DECIMAL(12,2) DEFAULT 0.00,
  bond_months          INT DEFAULT 0,
  location             VARCHAR(150) DEFAULT 'Remote',
  employment_type      VARCHAR(50) DEFAULT 'Full-Time',
  openings             INT DEFAULT 1,
  hiring_manager_name  VARCHAR(150) DEFAULT 'Not Assigned',
  hiring_manager_email VARCHAR(255) DEFAULT 'noreply@company.com',
  status               VARCHAR(30) NOT NULL DEFAULT 'Open',
  created_at           DATETIME2 DEFAULT GETUTCDATE(),
  updated_at           DATETIME2 DEFAULT GETUTCDATE(),
  CONSTRAINT chk_salary     CHECK (salary_min <= salary_max),
  CONSTRAINT chk_experience CHECK (experience_min_yrs <= experience_max_yrs),
  FOREIGN KEY (company_id) REFERENCES tbl_cp_mcompany(company_id) ON DELETE NO ACTION
);

-- =====================================================
-- ADDRESS TABLES
-- =====================================================

CREATE TABLE tbl_cp_student_address (
  row_id         INT NOT NULL IDENTITY(1,1) PRIMARY KEY,
  address_id     INT NOT NULL UNIQUE,
  student_id     INT NOT NULL,
  address_line_1 VARCHAR(255) NOT NULL,
  address_line_2 VARCHAR(255) DEFAULT '',
  care_of        VARCHAR(255) DEFAULT '',
  landmark       VARCHAR(255) DEFAULT 'No Landmark',
  pincode_id     INT NOT NULL,
  latitude       DECIMAL(10,8) DEFAULT 0.00000000,
  longitude      DECIMAL(11,8) DEFAULT 0.00000000,
  address_type   VARCHAR(50) NOT NULL DEFAULT 'current',
  address_expiry DATE DEFAULT '9999-12-31',
  created_at     DATETIME2 DEFAULT GETUTCDATE(),
  updated_at     DATETIME2 DEFAULT GETUTCDATE(),
  FOREIGN KEY (student_id) REFERENCES tbl_cp_student(student_id) ON DELETE NO ACTION,
  FOREIGN KEY (pincode_id) REFERENCES tbl_cp_mpincodes(pincode_id) ON DELETE NO ACTION
);

CREATE TABLE tbl_cp_college_address (
  row_id         INT NOT NULL IDENTITY(1,1) PRIMARY KEY,
  address_id     INT NOT NULL UNIQUE,
  college_id     INT NOT NULL,
  address_line_1 VARCHAR(255) NOT NULL,
  address_line_2 VARCHAR(255) DEFAULT '',
  landmark       VARCHAR(255) DEFAULT 'No Landmark',
  pincode_id     INT NOT NULL,
  latitude       DECIMAL(10,8) DEFAULT 0.00000000,
  longitude      DECIMAL(11,8) DEFAULT 0.00000000,
  address_type   VARCHAR(50) NOT NULL DEFAULT 'campus',
  created_at     DATETIME2 DEFAULT GETUTCDATE(),
  updated_at     DATETIME2 DEFAULT GETUTCDATE(),
  FOREIGN KEY (college_id) REFERENCES tbl_cp_mcolleges(college_id) ON DELETE NO ACTION,
  FOREIGN KEY (pincode_id) REFERENCES tbl_cp_mpincodes(pincode_id) ON DELETE NO ACTION
);

CREATE TABLE tbl_cp_company_address (
  row_id         INT NOT NULL IDENTITY(1,1) PRIMARY KEY,
  address_id     INT NOT NULL UNIQUE,
  company_id     INT NOT NULL,
  address_line_1 VARCHAR(255) NOT NULL,
  address_line_2 VARCHAR(255) DEFAULT '',
  landmark       VARCHAR(255) DEFAULT 'No Landmark',
  pincode_id     INT NOT NULL,
  latitude       DECIMAL(10,8) DEFAULT 0.00000000,
  longitude      DECIMAL(11,8) DEFAULT 0.00000000,
  address_type   VARCHAR(50) NOT NULL DEFAULT 'registered',
  created_at     DATETIME2 DEFAULT GETUTCDATE(),
  updated_at     DATETIME2 DEFAULT GETUTCDATE(),
  FOREIGN KEY (company_id) REFERENCES tbl_cp_mcompany(company_id) ON DELETE NO ACTION,
  FOREIGN KEY (pincode_id) REFERENCES tbl_cp_mpincodes(pincode_id) ON DELETE NO ACTION
);

-- =====================================================
-- ROUND CONFIGURATION PER JD TABLES
-- =====================================================

CREATE TABLE tbl_cp_jd_round_config (
  row_id          INT NOT NULL IDENTITY(1,1) PRIMARY KEY,
  round_config_id INT NOT NULL UNIQUE,
  jd_id           INT NOT NULL,
  round_number    TINYINT NOT NULL,
  round_label     VARCHAR(100) NOT NULL DEFAULT 'Round',
  is_exam         BIT NULL,
  created_at      DATETIME2 DEFAULT GETUTCDATE(),
  updated_at      DATETIME2 DEFAULT GETUTCDATE(),
  UNIQUE (jd_id, round_number),
  UNIQUE (jd_id, round_label),
  FOREIGN KEY (jd_id) REFERENCES tbl_cp_job_description(jd_id) ON DELETE NO ACTION
);

CREATE TABLE tbl_cp_m2m_jd_round_module (
  row_id          INT NOT NULL IDENTITY(1,1) PRIMARY KEY,
  jd_round_mod_id INT NOT NULL UNIQUE,
  round_config_id INT NOT NULL,
  module_id       INT NOT NULL,
  weightage       DECIMAL(5,4) NOT NULL DEFAULT 0.1,
  difficulty_id   INT NULL,
  is_mandatory    BIT NULL,
  created_at      DATETIME2 DEFAULT GETUTCDATE(),
  updated_at      DATETIME2 DEFAULT GETUTCDATE(),
  UNIQUE (round_config_id, module_id),
  FOREIGN KEY (round_config_id) REFERENCES tbl_cp_jd_round_config(round_config_id) ON DELETE NO ACTION,
  FOREIGN KEY (module_id)       REFERENCES tbl_cp_mmodule(module_id) ON DELETE NO ACTION,
  FOREIGN KEY (difficulty_id)   REFERENCES tbl_cp_mdifficulty(difficulty_id) ON DELETE NO ACTION
);

-- =====================================================
-- RECRUITMENT DRIVE TABLE
-- =====================================================

CREATE TABLE tbl_cp_recruitment_drive (
  row_id      INT NOT NULL IDENTITY(1,1) PRIMARY KEY,
  drive_id    INT NOT NULL UNIQUE,
  drive_name  VARCHAR(255) NOT NULL,
  jd_id       INT NOT NULL,
  start_date  DATE DEFAULT '1900-01-01',
  end_date    DATE DEFAULT '9999-12-31',
  description TEXT,
  status      VARCHAR(30) NOT NULL DEFAULT 'Active',
  created_at  DATETIME2 DEFAULT GETUTCDATE(),
  updated_at  DATETIME2 DEFAULT GETUTCDATE(),
  CONSTRAINT chk_drive_dates CHECK (start_date <= end_date),
  FOREIGN KEY (jd_id) REFERENCES tbl_cp_job_description(jd_id) ON DELETE NO ACTION
);

-- =====================================================
-- APPLICATION TABLES
-- =====================================================

CREATE TABLE tbl_cp_application (
  row_id           INT NOT NULL IDENTITY(1,1) PRIMARY KEY,
  application_id   INT NOT NULL UNIQUE,
  student_id       INT NOT NULL,
  drive_id         INT NOT NULL,
  serial_no        INT NOT NULL,
  application_date DATE NOT NULL DEFAULT CAST(GETUTCDATE() AS DATE),
  status           VARCHAR(50) NOT NULL DEFAULT 'Applied',
  created_at       DATETIME2 DEFAULT GETUTCDATE(),
  updated_at       DATETIME2 DEFAULT GETUTCDATE(),
  UNIQUE (student_id, drive_id),
  UNIQUE (drive_id, serial_no),
  FOREIGN KEY (student_id) REFERENCES tbl_cp_student(student_id) ON DELETE NO ACTION,
  FOREIGN KEY (drive_id)   REFERENCES tbl_cp_recruitment_drive(drive_id) ON DELETE NO ACTION
);

CREATE TABLE tbl_cp_application_status_history (
  row_id         INT NOT NULL IDENTITY(1,1) PRIMARY KEY,
  history_id     INT NOT NULL UNIQUE,
  application_id INT NOT NULL,
  status         VARCHAR(50) NOT NULL DEFAULT 'Applied',
  changed_date   DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
  created_at     DATETIME2 DEFAULT GETUTCDATE(),
  updated_at     DATETIME2 DEFAULT GETUTCDATE(),
  FOREIGN KEY (application_id) REFERENCES tbl_cp_application(application_id) ON DELETE NO ACTION
);

-- =====================================================
-- EXAM SESSION TABLES
-- =====================================================

CREATE TABLE tbl_cp_exam_session (
  row_id          INT NOT NULL IDENTITY(1,1) PRIMARY KEY,
  exam_session_id INT NOT NULL UNIQUE,
  application_id  INT NOT NULL,
  round_config_id INT NOT NULL,
  attendance_id   INT NOT NULL,
  exam_date       DATE DEFAULT '1900-01-01',
  exam_time       TIME DEFAULT '00:00:00',
  cutoff_pct      DECIMAL(5,4) DEFAULT 0.4000,
  correct_count   INT DEFAULT 0,
  incorrect_count INT DEFAULT 0,
  total_questions INT DEFAULT 0,
  score_pct       DECIMAL(5,4) DEFAULT 0.0000,
  result_id       INT NULL,
  feedback        TEXT,
  created_at      DATETIME2 DEFAULT GETUTCDATE(),
  updated_at      DATETIME2 DEFAULT GETUTCDATE(),
  CONSTRAINT chk_score_pct CHECK (score_pct >= 0 AND score_pct <= 1),
  UNIQUE (application_id, round_config_id),
  FOREIGN KEY (application_id)  REFERENCES tbl_cp_application(application_id) ON DELETE NO ACTION,
  FOREIGN KEY (round_config_id) REFERENCES tbl_cp_jd_round_config(round_config_id) ON DELETE NO ACTION,
  FOREIGN KEY (attendance_id)   REFERENCES tbl_cp_mattendance(attendance_id) ON DELETE NO ACTION,
  FOREIGN KEY (result_id)       REFERENCES tbl_cp_mround_result(result_id) ON DELETE NO ACTION
);

CREATE TABLE tbl_cp_m2m_exam_question_response (
  row_id          INT NOT NULL IDENTITY(1,1) PRIMARY KEY,
  response_id     INT NOT NULL UNIQUE,
  exam_session_id INT NOT NULL,
  question_id     INT NOT NULL,
  option_id       INT NULL,
  is_correct      BIT NULL,
  marks_awarded   DECIMAL(5,2) DEFAULT 0.00,
  created_at      DATETIME2 DEFAULT GETUTCDATE(),
  updated_at      DATETIME2 DEFAULT GETUTCDATE(),
  UNIQUE (exam_session_id, question_id),
  FOREIGN KEY (exam_session_id) REFERENCES tbl_cp_exam_session(exam_session_id) ON DELETE NO ACTION,
  FOREIGN KEY (question_id)     REFERENCES tbl_cp_mquestions(question_id) ON DELETE NO ACTION,
  FOREIGN KEY (option_id)       REFERENCES tbl_cp_m2m_question_options(option_id) ON DELETE NO ACTION
);

-- =====================================================
-- INTERVIEW SESSION TABLES
-- =====================================================

CREATE TABLE tbl_cp_interview_session (
  row_id            INT NOT NULL IDENTITY(1,1) PRIMARY KEY,
  session_id        INT NOT NULL UNIQUE,
  application_id    INT NOT NULL,
  round_config_id   INT NOT NULL,
  interviewer_id    INT NULL,
  attendance_id     INT NOT NULL,
  session_date      DATE DEFAULT '1900-01-01',
  session_time      TIME DEFAULT '00:00:00',
  bonus_marks       DECIMAL(5,2) DEFAULT 0.00,
  total_score       DECIMAL(6,2) DEFAULT 0.00,
  result_id         INT NULL,
  comments          TEXT,
  internal_feedback TEXT,
  external_feedback TEXT,
  created_at        DATETIME2 DEFAULT GETUTCDATE(),
  updated_at        DATETIME2 DEFAULT GETUTCDATE(),
  UNIQUE (application_id, round_config_id),
  FOREIGN KEY (application_id)  REFERENCES tbl_cp_application(application_id) ON DELETE NO ACTION,
  FOREIGN KEY (round_config_id) REFERENCES tbl_cp_jd_round_config(round_config_id) ON DELETE NO ACTION,
  FOREIGN KEY (interviewer_id)  REFERENCES tbl_cp_minterviewer(interviewer_id) ON DELETE NO ACTION,
  FOREIGN KEY (attendance_id)   REFERENCES tbl_cp_mattendance(attendance_id) ON DELETE NO ACTION,
  FOREIGN KEY (result_id)       REFERENCES tbl_cp_mround_result(result_id) ON DELETE NO ACTION
);

CREATE TABLE tbl_cp_m2m_session_module_score (
  row_id          INT NOT NULL IDENTITY(1,1) PRIMARY KEY,
  score_id        INT NOT NULL UNIQUE,
  session_id      INT NOT NULL,
  module_id       INT NOT NULL,
  correct_count   INT DEFAULT 0,
  incorrect_count INT DEFAULT 0,
  total_questions INT DEFAULT 0,
  score_sum       DECIMAL(6,2) NOT NULL DEFAULT 0.00,
  created_at      DATETIME2 DEFAULT GETUTCDATE(),
  updated_at      DATETIME2 DEFAULT GETUTCDATE(),
  UNIQUE (session_id, module_id),
  FOREIGN KEY (session_id) REFERENCES tbl_cp_interview_session(session_id) ON DELETE NO ACTION,
  FOREIGN KEY (module_id)  REFERENCES tbl_cp_mmodule(module_id) ON DELETE NO ACTION
);

CREATE TABLE tbl_cp_m2m_session_question_response (
  row_id        INT NOT NULL IDENTITY(1,1) PRIMARY KEY,
  response_id   INT NOT NULL UNIQUE,
  session_id    INT NOT NULL,
  question_id   INT NOT NULL,
  is_correct    BIT NULL,
  marks_awarded DECIMAL(5,2) DEFAULT 0.00,
  created_at    DATETIME2 DEFAULT GETUTCDATE(),
  updated_at    DATETIME2 DEFAULT GETUTCDATE(),
  UNIQUE (session_id, question_id),
  FOREIGN KEY (session_id)  REFERENCES tbl_cp_interview_session(session_id) ON DELETE NO ACTION,
  FOREIGN KEY (question_id) REFERENCES tbl_cp_mquestions(question_id) ON DELETE NO ACTION
);

-- =====================================================
-- INDEXES
-- =====================================================

CREATE INDEX idx_question_module        ON tbl_cp_mquestions(module_id);
CREATE INDEX idx_question_difficulty    ON tbl_cp_mquestions(difficulty_id);
CREATE INDEX idx_question_type          ON tbl_cp_mquestions(question_type);

CREATE INDEX idx_jd_company             ON tbl_cp_job_description(company_id);
CREATE INDEX idx_jd_job_role            ON tbl_cp_job_description(job_role);
CREATE INDEX idx_jd_status              ON tbl_cp_job_description(status);

CREATE INDEX idx_student_address_type   ON tbl_cp_student_address(address_type);
CREATE INDEX idx_round_config_jd        ON tbl_cp_jd_round_config(jd_id);
CREATE INDEX idx_jrm_round_config       ON tbl_cp_m2m_jd_round_module(round_config_id);
CREATE INDEX idx_jrm_module             ON tbl_cp_m2m_jd_round_module(module_id);
CREATE INDEX idx_drive_jd               ON tbl_cp_recruitment_drive(jd_id);
CREATE INDEX idx_drive_status           ON tbl_cp_recruitment_drive(status);
CREATE INDEX idx_application_student    ON tbl_cp_application(student_id);
CREATE INDEX idx_application_drive      ON tbl_cp_application(drive_id);
CREATE INDEX idx_application_status     ON tbl_cp_application(status);
CREATE INDEX idx_status_history_app     ON tbl_cp_application_status_history(application_id);
CREATE INDEX idx_exam_result            ON tbl_cp_exam_session(result_id);
CREATE INDEX idx_exam_qr_question       ON tbl_cp_m2m_exam_question_response(question_id);
CREATE INDEX idx_session_application    ON tbl_cp_interview_session(application_id);
CREATE INDEX idx_session_round_config   ON tbl_cp_interview_session(round_config_id);
CREATE INDEX idx_session_interviewer    ON tbl_cp_interview_session(interviewer_id);
CREATE INDEX idx_session_result         ON tbl_cp_interview_session(result_id);
CREATE INDEX idx_session_date           ON tbl_cp_interview_session(session_date);
CREATE INDEX idx_sms_module             ON tbl_cp_m2m_session_module_score(module_id);
CREATE INDEX idx_sqr_question           ON tbl_cp_m2m_session_question_response(question_id);
