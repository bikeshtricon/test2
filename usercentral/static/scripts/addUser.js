$(document).ready(function () {
	$("input:radio[name=usertype]").click(function() {
   		if($(this).val()=="carrieruser"){
   			$(".form-signin  div.userCarrierGroup select").css('border-color','#CCCCCC');
   			$(".form-signin  div.userCarrierGroup").show();
   		}	
      	else {
      		$(".form-signin  div.userCarrierGroup").hide();
      	}
   		$(".form-signin  div.userCarrierGroup").next(".mandatory_field").hide();
   	});
	$("button.addFormReset").click(function() {
		$(".form-signin .get_value").each(function(){
			var selectedElement = $(this);
			selectedElement.css('border-color','#CCCCCC');
			selectedElement.parent().next(".mandatory_field").hide();
		});
		$(".form-signin  div.userCarrierGroup").hide();
	});
});
$(".form-signin").submit(function() {
	var error_field = 0;
	$(".form-signin .get_value").each(function(){
		var selectedElement = $(this);
		if(selectedElement.val()==""){
			if(selectedElement.attr("name")!="usergroup" || $('input:radio[name=usertype]:checked').val()=="carrieruser"){
				error_field = 1;
				selectedElement.css('border-color','#E00000');
				selectedElement.parent().next(".mandatory_field").show();
			}
		}
		else {
			if(selectedElement.attr("name")=="useremail"){
				var user_emailID=selectedElement.val();
				var atpos=user_emailID.indexOf("@");
				var dotpos=user_emailID.lastIndexOf(".");
				if (atpos<1 || dotpos<atpos+2 || dotpos+2>=user_emailID.length){
					error_field = 1;
					selectedElement.css('border-color','#E00000');
					selectedElement.parent().next(".mandatory_field").show();
				}
				else {
					selectedElement.css('border-color','#CCCCCC');
					selectedElement.parent().next(".mandatory_field").hide();
				}
			}
			else {
				selectedElement.css('border-color','#CCCCCC');
				selectedElement.parent().next(".mandatory_field").hide();
			}
		}
	});
	setTimeout(function(){
		if(error_field == 0){
			$("#interstitial").show();
			var userEmail = $('[name="useremail"]').val();
			var userName = $('[name="username"]').val();
			var userType = $('[name="usertype"]').val();
			var userProgram = $('[name="userprogram"]').val();
			var userGroup = $('[name="usergroup"]').val();
			$.ajax({
				url: '/addUserSubmit',
				type: 'POST',
				data: { useremail: userEmail, username: userName, usertype: userType, userprogram: userProgram, usergroup: userGroup },
	           	success: function(data){
	           		$("#interstitial").hide();
	           		if(data['result']=="success"){
	           			//$("div.addUserMessageContainer").html('<div class="alert alert-danger alert-dismissable"><button type="button" class="close" data-dismiss="alert" aria-hidden="true">&times;</button><div class="messageHeader"><strong>Failure!</strong></div><b>Unable to add '+ userName +' as a new user!</b> Please try again.</div>');
	           			$("div.addUserMessageContainer").html('<div class="alert alert-success alert-dismissable"><button type="button" class="close" data-dismiss="alert" aria-hidden="true">&times;</button><div class="messageHeader"><strong>Success!</strong></div><b>'+ data['username'] +' has been created!</b> An email has been sent to the user to complete the setup process.</div>');
	            	   $("div.container .addUserConfirmMessage").css("color","#2A8F2A");
	            	   $("div.container .addUserConfirmMessage").show();
	               }
	               else if(data['result']=="fail"){
	            	   $("div.addUserMessageContainer").html('<div class="alert alert-danger alert-dismissable"><button type="button" class="close" data-dismiss="alert" aria-hidden="true">&times;</button><div class="messageHeader"><strong>Failure!</strong></div>'+ data['message'] +'</div>');
	            	   $("div.container .addUserConfirmMessage").css("color","#E22525");
	            	   $("div.container .addUserConfirmMessage").show();
	               }
	           	}
	        });
		}
	},100);
	return false; // avoid to execute the actual submit of the form.
});