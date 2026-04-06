# Import model classes so SQLAlchemy metadata is fully registered at startup.
from .student_model import Student
from .education_model import StudentSchool, StudentEducation
from .workexp_model import StudentWorkExp
from .project_model import StudentProject
from .address_model import StudentAddress
from .m2m_model import (
	StudentSkill,
	StudentLanguage,
	StudentInterest,
	StudentCertification,
	StudentProjectSkill,
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
	"StudentSkill",
	"StudentLanguage",
	"StudentInterest",
	"StudentCertification",
	"StudentProjectSkill",
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
