import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { cleanup, render as testRender, screen, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { MemoryRouter } from "react-router-dom";
import { TeacherOccurrencePage } from "../TeacherOccurrencePage";
import { backendApi } from "../../../../shared/api/backendApi";
import { teacherOccurrenceApi } from "../../../../shared/api/teacherOccurrenceApi";
import { authService } from "../../../school-manager/be1/services/authService";

function render(ui: ReactNode) { return testRender(<MemoryRouter>{ui}</MemoryRouter>); }

beforeEach(() => { window.sketch2lifeConfig={organizationId:"org-test"}; window.sketch2lifeAuth={getIdToken:vi.fn(async()=>"token")} as never; vi.spyOn(authService,"observe").mockImplementation(cb=>{cb({uid:"teacher"} as never); return () => undefined;}); });
afterEach(() => {cleanup();vi.restoreAllMocks();window.sketch2lifeAuth=undefined;window.sketch2lifeConfig=undefined;});
it.each([
 ["DRAFT","AVAILABLE",false,false], ["APPROVED","AVAILABLE",true,false], ["SAMPLE_AVAILABLE","AVAILABLE",true,false], ["SAMPLE_USED","AVAILABLE",true,true], ["DRAFT","CLAIMED",false,true], ["APPROVED","CLAIMED",true,true], ["COMPLETED","AVAILABLE",false,false],
])("entry links for state %s and slot %s",async(state,slot,sample,projection)=>{
 const occurrence={contract:"LessonOccurrenceV1",occurrence_id:"occ-1",class_id:"class-1",title:"Buổi dạy",scheduled_date:null,state,revision:1,responsible_teacher_ref:"t",lesson_version_ref:null,lesson_version_no:null,approved_plan:null,sample_video:{slot_state:slot,claimed_at:null,run_ref:null},created_at:""};
 vi.spyOn(backendApi,"assignments").mockResolvedValue({assignments:[{role:"teacher",class_id:"class-1",active:true}]} as never);
 vi.spyOn(backendApi,"classes").mockResolvedValue({items:[{class_id:"class-1",display_name:"Lớp"}]} as never);
 vi.spyOn(backendApi,"lessons").mockResolvedValue({items:[]} as never);
 vi.spyOn(teacherOccurrenceApi,"list").mockResolvedValue({items:[occurrence],next_cursor:null} as never);
 vi.spyOn(teacherOccurrenceApi,"get").mockResolvedValue({data:occurrence,etag:'"1"',notModified:false} as never);
 vi.spyOn(teacherOccurrenceApi,"listDocuments").mockResolvedValue({items:[],next_cursor:null} as never);
 vi.spyOn(teacherOccurrenceApi,"listPlans").mockResolvedValue({items:[],next_cursor:null} as never);
 render(<TeacherOccurrencePage />); await screen.findByRole("heading",{name:"Buổi dạy"});
 await waitFor(() => expect(Boolean(screen.queryByRole("link",{name:"Video mẫu"}))).toBe(sample));
 await waitFor(() => expect(Boolean(screen.queryByRole("link",{name:"Chiếu cho lớp"}))).toBe(projection));
});
