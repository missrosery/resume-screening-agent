export interface Position {
  id: string;
  title: string;
  department: string | null;
  requirements: string | null;
  created_at: string;
}

export interface ParsedResumeData {
  name: string;
  phone?: string | null;
  email?: string | null;
  city?: string | null;
  job_intention?: string | null;
  highest_degree: string;
  work_years?: number | null;
  skills: string[];
  certifications: string[];
  summary: string;
  education?: Array<{
    school: string;
    degree: string;
    major: string;
    start_date?: string | null;
    end_date?: string | null;
  }>;
  work_experience?: Array<{
    company: string;
    position: string;
    duration: string;
    responsibilities: string[];
    achievements: string[];
  }>;
}

export interface Resume {
  id: string;
  position_id: string;
  file_name: string;
  file_hash?: string | null;
  file_type: string;
  parse_status: string;
  parsed_data: ParsedResumeData | null;
  parse_error?: string | null;
  duplicate?: boolean;
  created_at: string;
}

export interface RankedResume {
  resume_id: string;
  name: string;
  match_score: number;
  match_reasons: string[];
  weaknesses: string[];
  highest_degree: string;
  work_years: number | null;
  skills: string[];
}

export interface InterviewQuestionGroup {
  category: "技术深挖" | "项目复盘" | "行为判断";
  questions: string[];
}

export interface ScreeningMessage {
  type: "thinking" | "tool_call" | "text" | "resume_card" | "done" | "error";
  content: string;
  data?: RankedResume;
}

export interface Session {
  id: string;
  position_id: string;
  title: string;
  created_at: string;
}
