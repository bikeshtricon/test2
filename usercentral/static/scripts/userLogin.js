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
	if(error_field == 1){
		return false;
	}
});