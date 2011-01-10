import dispatch._
import Http._
import org.apache.http.params._
import java.lang.RuntimeException
import java.lang.Runtime.getRuntime
import java.lang.Thread.sleep
import java.util.Date
import org.slf4j.LoggerFactory

object HeaterWatchdog {
  val http = new Http

  val targetService = :/("bang", 9056)

  // d4 is configured in devices.n3
  var targetPath = "pin/d4"
  val tooLongSeconds = 50 * 60
  var pollSeconds = 60
 
  def main(args: Array[String]) {
    val log = LoggerFactory.getLogger("main")
    val p = http.client.getParams()
    HttpConnectionParams.setConnectionTimeout(p, 2000)
    HttpConnectionParams.setSoTimeout(p, 2000)

    pollForever()
  }

  def pollForever() {
    var highSince: Option[Long] = None
    while (true) {
      val level = getPin
      val now = new Date().getTime
      if (level) {
	highSince = highSince match {
	  case None => Some(now)
	  case _ => highSince
	}
      } else {
	highSince = None
      }
      log.info("now at "+level+", high since "+highSince)
      if (highSince.exists((h) => (now - h) > (tooLongSeconds * 1000))) {
	shutdownHeater()
        // freeze after, since we do need it to listen to our command. But
        // now there is a race to freeze it before anything else turns the
        // output back on
        freezeArduinoDriver()
	return
      }

      sleep(pollSeconds * 1000)
    }
  }

  def shutdownHeater() {
    http(targetService / targetPath / "mode" <<< "output" >|)
    http(targetService / targetPath <<< "0" >|)
  }

  def freezeArduinoDriver() {
    // i don't want it to restart, but i also want no chance of it sending
    // a 1 again until someone can investigate. This does freeze all other
    // outputs, but hopefully they're not as serious
    http(targetService / "pid" >- {pid => 
      log.info("killing "+pid)
      kill(pid.toInt)
    })
  }

  def getPin() = http.x(targetService / targetPath as_str) != "0"

  def kill(pid: Int) {
    val ret = getRuntime.exec(Array(
      "/bin/kill", "-STOP", pid.toString)).waitFor    
    if (ret != 0) {
      throw new RuntimeException("kill(pid="+pid+") failed ("+ret+")")
    }
  }
}
