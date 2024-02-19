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
  @Input() themeClass:string = '';
  
  userUrl : string = "";

  constructor(private configService: ConfigService) {}

  OnSubmitUrl(){
    let handleUrl = new HandleUrlService();
    let userUrl : string = handleUrl.OnSubmitUrl(this.userUrl);
    if (userUrl.length > 0) {
      // See: HandleUrlService for control logic.
      // Not DRY... but we don't want to make useless queries.
      this.configService.getArticle(userUrl);
    }
  }
}
