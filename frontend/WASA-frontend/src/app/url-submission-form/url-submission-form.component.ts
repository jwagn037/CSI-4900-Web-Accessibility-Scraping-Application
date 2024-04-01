import { Component, Input} from '@angular/core';
import { FormsModule } from '@angular/forms';
import { HandleUrlService } from '../Services/handle-url.service';
import { ConfigService } from '../Services/config.service';
import { NgClass } from '@angular/common';

@Component({
  selector: 'app-url-submission-form',
  standalone: true,
  imports: [FormsModule,
  NgClass],
  templateUrl: './url-submission-form.component.html',
  styleUrl: './url-submission-form.component.css'
})

export class UrlSubmissionFormComponent {
  @Input() themeClass:string = ''; // from landing component
  @Input() btnTheme:string = ''; // from landing component
  getImages:boolean = true;
  generateAltText:boolean = false;
  
  userUrl : string = "";

  constructor(private configService: ConfigService) {}

  ngOnInit() {
    const savedGetImagesSetting = localStorage.getItem('getImages-setting');
    const savedGenerateAltTextSetting = localStorage.getItem('generateAltText-setting');

    if (!Object.is(null, savedGetImagesSetting)) {
      if (savedGetImagesSetting == "true") {
        this.getImages = true;
      } else {
        this.getImages = false;
      }
    }

    if (!Object.is(null, savedGenerateAltTextSetting)) {
      if (savedGenerateAltTextSetting == "true") {
        this.generateAltText = true;
      } else {
        this.generateAltText = false;
      }
    }
  }

  toggleGetImages() {
    this.getImages = !this.getImages;
    localStorage.setItem('getImages-setting', String(this.getImages));
  }

  toggleGenerateAltText() {
    this.generateAltText = !this.generateAltText;
    localStorage.setItem('generateAltText-setting', String(this.generateAltText));
  }

  OnSubmitUrl(){
    let handleUrl = new HandleUrlService();
    let userUrl : string = handleUrl.OnSubmitUrl(this.userUrl);
    console.log(userUrl);
    if (userUrl.length > 0) {
      // See HandleUrlService for control logic.
      this.configService.getArticle(userUrl, this.getImages, this.generateAltText);
    }
  }
}
