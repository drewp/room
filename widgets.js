// import Nevow.Athena

if (typeof RoomWidget == 'undefined') {
    RoomWidget = {};
}

RoomWidget.Slider = Nevow.Athena.Widget.subclass('RoomWidget.Slider');
RoomWidget.Slider.methods(
    function __init__(self, node) {

      RoomWidget.Slider.upcall(self, '__init__', node);

      self.callRemote('getName').addCallback(function setupSlider(name) {
    
	self.name = name
	  self.width = 200;
	self.slider = YAHOO.widget.Slider.getHorizSlider("athenaid:" + self.objectID + "-sliderbg", "athenaid:" + self.objectID + "-sliderthumb", 0, self.width); 

	self.slider.subscribe("change", function (offset) {
	  var val = offset / self.width;
	  self.slider.lock()
	  self.callRemote('sliderChange', val).addCallback(function (result) { self.slider.unlock(); });
	});
      });
    
    },
    function setValue(self, val) {
      console.log("server said to set value", self.name, val);
      self.slider.setValue(val);
    }
);

      //function bsSliderChange(sliderObj, val, newPos){ 
      //    server.handle('sliderChange', sliderObj.fieldName, val);
      //}

