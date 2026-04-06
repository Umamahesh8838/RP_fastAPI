# Import model classes so SQLAlchemy metadata is fully registered at startup.
from .student_model import Student
from .education_model import StudentSchool, StudentEducation
from .workexp_model import StudentWorkExp
from .project_model import StudentProject
from .address_model import StudentAddress
from .m2m_model import (
	M2MStudentSkill,
	M2MStudentLanguage,
	M2MStudentInterest,
	M2MStudentCertification,
	M2MProjectSkill,
)
from .master_model import (
	MasterSalutation,
	MasterLanguage,
	MasterInterest,
	MasterCourse,
	MasterCollege,
	MasterCertification,
	MasterSkill,
	MasterCountry,
	MasterState,
	MasterCity,
	MasterPincode,
	ResumeHash,
)

__all__ = [
	"Student",
	"StudentSchool",
	"StudentEducation",
	"StudentWorkExp",
	"StudentProject",
	"StudentAddress",
	"M2MStudentSkill",
	"M2MStudentLanguage",
	"M2MStudentInterest",
	"M2MStudentCertification",
	"M2MProjectSkill",
	"MasterSalutation",
	"MasterLanguage",
	"MasterInterest",
	"MasterCourse",
	"MasterCollege",
	"MasterCertification",
	"MasterSkill",
	"MasterCountry",
	"MasterState",
	"MasterCity",
	"MasterPincode",
	"ResumeHash",
]
