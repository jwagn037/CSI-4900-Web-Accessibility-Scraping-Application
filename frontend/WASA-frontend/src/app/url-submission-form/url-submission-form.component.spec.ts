import { ComponentFixture, TestBed } from '@angular/core/testing';

import { UrlSubmissionFormComponent } from './url-submission-form.component';

describe('UrlSubmissionFormComponent', () => {
  let component: UrlSubmissionFormComponent;
  let fixture: ComponentFixture<UrlSubmissionFormComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [UrlSubmissionFormComponent]
    })
    .compileComponents();
    
    fixture = TestBed.createComponent(UrlSubmissionFormComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
