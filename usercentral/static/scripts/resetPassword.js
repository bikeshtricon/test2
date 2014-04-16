$(".form-signin").submit(function() {
	var error_field = 0;
	$(".form-signin .get_value").each(function(){
		var selectedElement = $(this);
		if(selectedElement.val()==""){
			error_field = 1;
			selectedElement.css('border-color','#E00000');
			selectedElement.parent().next(".mandatory_field").show();
		}
		else {
			selectedElement.css('border-color','#CCCCCC');
			selectedElement.parent().next(".mandatory_field").hide();
		}
	});
	if(error_field == 0){
		if($("input.newPassword").val() == $("input.confirmPassword").val()){
			var str = $("input.newPassword").val();
			if(str){
			    str = str.replace(/ /g,'');
				var patt=/^(?=.*\d)(?=.*[a-z])(?=.*[A-Z]).{8,32}$/; 
				var result = patt.test(str);
				if(!result){
					$("div.resetPasswordMessage").html('<div class="alert alert-danger alert-dismissable"><button type="button" class="close" data-dismiss="alert" aria-hidden="true">&times;</button><div class="messageHeader"><strong>Failure!</strong></div><b>Password doesn\'t meet required conditions!</b></div>');
				    return false;
				}
				else{
				   return true;
				}
			}
		}
		else {
			$("div.resetPasswordMessage").html('<div class="alert alert-danger alert-dismissable"><button type="button" class="close" data-dismiss="alert" aria-hidden="true">&times;</button><div class="messageHeader"><strong>Failure!</strong></div><b>new password and confirm password should be same!</b></div>');
			return false;
		}
	}
	return false;
});