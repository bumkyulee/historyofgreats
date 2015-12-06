function center(id){
	var $layerPopupObj = $('#'+id);
	var left = ( $(window).scrollLeft() + ($(window).width() - $layerPopupObj.width()) / 2 );
	var top = ( $(window).scrollTop() + ($(window).height() - $layerPopupObj.height()) / 2 );
	$layerPopupObj.css({'left':left,'top':top, 'position':'absolute'});
	$('body').css('position','relative').append($layerPopupObj);
}
function blockWheel()
{
	jQuery(window).on("mousewheel.disableScroll DOMMouseScroll.disableScroll touchmove.disableScroll", function(e) {
		e.preventDefault();
		return;
	});


	jQuery(window).on("keydown.disableScroll", function(e) {
		var eventKeyArray = [32, 33, 34, 35, 36, 37, 38, 39, 40];
		for (var i = 0; i < eventKeyArray.length; i++) {
			if (e.keyCode === eventKeyArray [i]) {
				e.preventDefault();
				return;
			}
		}
	});
}
function playWheel()
{
	jQuery(window).off(".disableScroll");
}

function detectMobile() {
   if(window.innerWidth <= 800 && window.innerHeight <= 600) {
     return true;
   } else {
     return false;
   }
}